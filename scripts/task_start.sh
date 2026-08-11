#!/usr/bin/env bash
# ============================================================================
# task_start.sh — 契約の取り込み開始を一つの操作にまとめる。
#
# 契約を受け取るたびに手で並べていた 4 行を 1 操作にする。
#
#   使い方:
#       source .venv/bin/activate && source scripts/load_env.sh
#       make task-start TASK=T-YYYY-MM-DD-slug
#       # または  bash scripts/task_start.sh T-YYYY-MM-DD-slug
#
# `source` の 2 行は残る。**make はサブシェルでレシピを動かすため、呼び出し元の
# シェルへ環境を返せない。** ここをまとめることは原理的にできない。
#
# **手数を減らすことが目的ではない。** 分岐名を人が打つ限り、契約の識別子と分岐名が
# ずれる余地が残る。実測では、分岐が現存する 23 契約のうち 10 件が手で短縮されていた
# （`feat/report-back` ← `T-2026-08-18-report-back-to-ledger` など）。
# **識別子から分岐名を機械的に導き、人が打たないようにすることが本題である。**
#
# 満たすべき不変条件:
#   1. 途中で失敗したら実行前の状態に戻る。分岐も一時ファイルも残さない
#   2. 既存の Makefile レシピを変更しない（追記のみ）
#   3. 資格情報の値を出力にも記録にも残さない。**存在の真偽だけを扱う**
#   4. 二度実行しても壊れない
#
# 終了コード:
#   0  成功
#   2  使い方の誤り（識別子が空・形式が不正）
#   3  前提が満たされていない（仮想環境・資格情報・作業ツリー・分岐の重複）
#   4  git 操作または取り込みの失敗（**巻き戻し済み**）
#
# `make` 経由では make 自身の終了コード（失敗時 2）になる。両方を見ること。
# ============================================================================
set -euo pipefail

BASE_REF="origin/phase0"      # 分岐の起点。契約はここから分岐して作業する
PAUSE_MARKER=".sync-pause"    # 常駐同期の抑止。既にあれば触れない

# 巻き戻しのために控える状態。**実行前の状態を必ず先に記録する。**
original_branch=""
created_branch=0
created_pause=0
branch=""

usage() {
    cat >&2 <<'USAGE'
使い方:
    source .venv/bin/activate && source scripts/load_env.sh
    make task-start TASK=T-YYYY-MM-DD-slug

識別子は T-YYYY-MM-DD-slug（slug は小文字英数とハイフン、3〜60 文字）。
分岐名は識別子から機械的に導く（feat/<slug>）。人が打たない。
USAGE
}

die() {  # die <終了コード> <本文...>
    local code="$1"; shift
    printf '[task-start] %s\n' "$*" >&2
    exit "${code}"
}

rollback() {
    # **自分が作ったものだけを消す。** 実行前からあったものには触れない。
    if [ "${created_pause}" -eq 1 ]; then
        rm -f "${PAUSE_MARKER}"
    fi
    if [ "${created_branch}" -eq 1 ] && [ -n "${original_branch}" ]; then
        git checkout -q "${original_branch}" || {
            printf '[task-start] 元の分岐へ戻れませんでした: %s\n' "${original_branch}" >&2
            printf '[task-start] 分岐 %s が残っています。手で確認してください\n' "${branch}" >&2
            return
        }
        git branch -q -D "${branch}" >/dev/null 2>&1 || {
            printf '[task-start] 分岐を消せませんでした: %s\n' "${branch}" >&2
            return
        }
    fi
    printf '[task-start] 実行前の状態へ戻しました\n' >&2
}

main() {
    cd "$(git rev-parse --show-toplevel)"

    # --- 1. 識別子の形式を検証する ---------------------------------------
    local task_id="${1-}"
    if [ -z "${task_id}" ]; then
        usage
        die 2 "識別子が指定されていません"
    fi
    if [[ ! "${task_id}" =~ ^T-[0-9]{4}-[0-9]{2}-[0-9]{2}-([a-z0-9-]{3,60})$ ]]; then
        usage
        die 2 "識別子の形式が不正です: ${task_id}"
    fi
    branch="feat/${BASH_REMATCH[1]}"

    # --- 2. 仮想環境が有効か ---------------------------------------------
    if [ -z "${VIRTUAL_ENV-}" ]; then
        die 3 "仮想環境が有効ではありません。先に source .venv/bin/activate を実行してください"
    fi

    # --- 3. 資格情報が「存在するか」。値は見ない・出さない ---------------
    if [ -z "${NOTION_API_KEY-}" ]; then
        die 3 "NOTION_API_KEY が未設定です。先に source scripts/load_env.sh を実行してください"
    fi

    # --- 4. 作業ツリーが汚れていないか -----------------------------------
    local dirty
    dirty="$(git status --porcelain | wc -l)"
    if [ "${dirty}" -ne 0 ]; then
        git status --short >&2
        die 3 "作業ツリーに未commitの変更が ${dirty} 件あります。片付けてから実行してください"
    fi

    # --- 5. 分岐が既に存在しないか ---------------------------------------
    if git rev-parse --verify --quiet "refs/heads/${branch}" >/dev/null; then
        die 3 "分岐が既に存在します: ${branch}（同じ契約を二度取り込もうとしています）"
    fi

    # ここから先は巻き戻しの対象になる。**実行前の状態を控える。**
    original_branch="$(git branch --show-current)"
    if [ -z "${original_branch}" ]; then
        die 3 "現在の分岐を特定できません（detached HEAD の可能性）"
    fi
    if [ -e "${PAUSE_MARKER}" ]; then
        created_pause=0        # 実行前からある。**巻き戻しで消してはならない**
    else
        created_pause=1
    fi

    # --- 6. 取得 ----------------------------------------------------------
    printf '[task-start] git fetch origin\n'
    if ! git fetch origin; then
        die 4 "git fetch に失敗しました"
    fi

    # --- 7. 分岐を作って切り替える ---------------------------------------
    printf '[task-start] 分岐を作成: %s（起点 %s）\n' "${branch}" "${BASE_REF}"
    if ! git checkout -q -b "${branch}" "${BASE_REF}"; then
        die 4 "分岐を作成できませんでした: ${branch}"
    fi
    created_branch=1

    # --- 8. 同期の抑止を置く ---------------------------------------------
    if [ "${created_pause}" -eq 1 ]; then
        touch "${PAUSE_MARKER}"
        printf '[task-start] %s を作成（報告まで終えたら rm -f %s）\n' "${PAUSE_MARKER}" "${PAUSE_MARKER}"
    else
        printf '[task-start] %s は実行前から存在するため触れません\n' "${PAUSE_MARKER}"
    fi

    # --- 9. 契約を取り込む。失敗したら 7 と 8 を巻き戻す ------------------
    printf '[task-start] 契約を取り込みます: %s\n' "${task_id}"
    if ! make task-notion "TASK=${task_id}"; then
        printf '[task-start] 取り込みに失敗しました。巻き戻します\n' >&2
        rollback
        exit 4
    fi

    printf '[task-start] 完了。分岐 %s で契約 %s の作業を開始できます\n' "${branch}" "${task_id}"
    printf '[task-start] 次: /task %s\n' "${task_id}"
}

main "$@"
