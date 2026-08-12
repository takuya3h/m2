"""到達性プローブ。**拒否と経路なしを区別できることが要点である。**

「全部つながらない」という結果は、経路が無いことと道具が壊れていることの
どちらでも起きる。区別できない道具で測ると、原因の見立てを検証できない。

    OPEN     相手の機器まで届き、その口が開いている
    REFUSED  相手の機器までは届いている。口が閉じている
    TIMEOUT  経路が無い（応答が返らない）
    OSERROR  上記以外。理由の文字列を付ける

使い方:

    .venv/bin/python tasks/T-2026-08-12-sync-audit-lecun/probe.py HOST:PORT [HOST:PORT ...]
"""

import socket
import sys


def probe(host, port, timeout=5.0):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, int(port)))
        return "OPEN"
    except socket.timeout:
        return "TIMEOUT"
    except ConnectionRefusedError:
        return "REFUSED"
    except OSError as e:
        return "OSERROR:" + (e.strerror or type(e).__name__).replace(" ", "_")
    finally:
        s.close()


if __name__ == "__main__":
    for spec in sys.argv[1:]:
        h, _, p = spec.rpartition(":")
        print(spec + " " + probe(h, p))
