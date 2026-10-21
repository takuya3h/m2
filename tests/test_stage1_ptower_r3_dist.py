"""The third round's several-GPU path: same frames, same gradients, own flips, rank 0 writes.

The CPU tests read the sampler, the loss scaling, the seeds and the dispatch directly.
The last test needs two GPUs and is skipped without them.
"""
import ast
import inspect
import socket
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

torch = pytest.importorskip("torch")
import stage1_ptower_r3 as r3  # noqa: E402
import stage1_ptower_r3_dist as dp  # noqa: E402
from omegaconf import OmegaConf  # noqa: E402
from torch import nn  # noqa: E402
from torch.utils.data import DataLoader, Dataset  # noqa: E402

# --- what ft_batch_size means -------------------------------------------------

def test_ft_batch_size_stays_the_batch_over_all_ranks():
    assert dp.per_rank_batch(16, 2) == 8
    assert dp.per_rank_batch(16, 4) == 4
    assert dp.per_rank_batch(16, 1) == 16
    # Both directions: a batch that does not split is refused before anything starts.
    with pytest.raises(ValueError):
        dp.per_rank_batch(16, 3)


def test_the_config_keeps_its_values_and_one_device():
    import yaml
    cfg = yaml.safe_load((ROOT / "configs/stage1_ptower_r3.yaml").read_text())
    assert cfg["ft_batch_size"] == 16 and cfg["ft_accum_steps"] == 4
    assert cfg["device"] == "cuda:0"


# --- which frames each rank sees ------------------------------------------------

def _epoch(size, batch, world, seed=42, epoch=1):
    shards = []
    for rank in range(world):
        sampler = dp.ShardedBatches(size, batch, rank, world, seed)
        sampler.set_epoch(epoch)
        shards.append(list(sampler))
    return shards


def _partition_problems(shards, size):
    """Duplicates and missing frames over all ranks' shards of one epoch."""
    seen = [i for rank in shards for batch in rank for i in batch]
    return {"duplicates": len(seen) - len(set(seen)),
            "missing": len(set(range(size)) - set(seen))}


def test_every_frame_is_used_once_per_epoch_over_all_ranks():
    size = 9657  # fold A's train frames; 9657 % 16 = 9
    shards = _epoch(size, 16, 2)
    assert _partition_problems(shards, size) == {"duplicates": 0, "missing": 0}
    assert len(shards[0]) == len(shards[1]) == -(-size // 16)
    # Both directions: one duplicated frame is caught.
    broken = [[list(b) for b in rank] for rank in shards]
    broken[1][0][0] = broken[0][0][0]
    assert _partition_problems(broken, size) == {"duplicates": 1, "missing": 1}


def test_global_batches_are_cut_like_the_one_gpu_loader_and_the_tail_is_kept():
    size, batch = 9657, 16
    sampler = dp.ShardedBatches(size, batch, 0, 2, 42)
    sampler.set_epoch(1)
    batches = sampler.global_batches()
    assert [len(b) for b in batches[:-1]] == [16] * (len(batches) - 1)
    assert len(batches[-1]) == 9
    assert [sampler.count(s) for s in (1, len(batches) - 1, len(batches))] == [16, 16, 9]
    # The tail is split 5 / 4 and each rank's shard is its slice of the same global batch.
    shards = _epoch(size, batch, 2)
    tail = sampler.global_batches()[-1]
    assert shards[0][-1] + shards[1][-1] == tail
    assert [len(shards[0][-1]), len(shards[1][-1])] == [5, 4]


def test_a_tail_that_would_leave_a_rank_empty_is_refused():
    with pytest.raises(ValueError):
        dp.ShardedBatches(17, 16, 0, 2, 42)
    # Both directions: a tail of two frames over two ranks is fine.
    dp.ShardedBatches(18, 16, 0, 2, 42)


def test_the_order_follows_the_seed_and_the_epoch_only():
    assert _epoch(100, 8, 2, seed=42, epoch=3) == _epoch(100, 8, 2, seed=42, epoch=3)
    assert _epoch(100, 8, 2, seed=42, epoch=3) != _epoch(100, 8, 2, seed=42, epoch=4)
    assert _epoch(100, 8, 2, seed=42, epoch=3) != _epoch(100, 8, 2, seed=43, epoch=3)


# --- the loss of the tail ----------------------------------------------------------

def _rank_gradient_mean(logits, y, parts, scaled):
    """What DDP hands every rank: the mean over ranks of each rank's gradient."""
    world, count, grads = len(parts), len(y), []
    for part in parts:
        x = logits[part].detach().clone().requires_grad_(True)
        loss = (dp.scaled_loss(x, y[part], count, world) if scaled
                else nn.functional.cross_entropy(x, y[part]))
        loss.backward()
        full = torch.zeros_like(logits)
        full[part] = x.grad
        grads.append(full)
    return sum(grads) / world


def test_the_scaled_loss_gives_the_one_gpu_gradient_on_an_uneven_tail():
    generator = torch.Generator().manual_seed(0)
    logits = torch.randn(9, 7, generator=generator, dtype=torch.float64)
    y = torch.randint(0, 7, (9,), generator=generator)
    x = logits.clone().requires_grad_(True)
    nn.functional.cross_entropy(x, y).backward()
    parts = [list(range(5)), list(range(5, 9))]
    assert torch.allclose(_rank_gradient_mean(logits, y, parts, True), x.grad, atol=1e-12)
    # Both directions: each rank's plain mean weighs the 4-frame shard too heavily.
    assert not torch.allclose(_rank_gradient_mean(logits, y, parts, False), x.grad, atol=1e-6)


# --- each rank's flips ------------------------------------------------------------

class _Flips(Dataset):
    """Draws as RandomHorizontalFlip does: one torch.rand per frame."""

    def __len__(self):
        return 64

    def __getitem__(self, index):
        return bool(torch.rand(1) < 0.5)


def _flips(seed, rank, workers=2):
    torch.manual_seed(seed)
    sampler = dp.ShardedBatches(64, 8, rank, 2, 42)
    loader = DataLoader(_Flips(), batch_sampler=sampler, num_workers=workers)
    return [bool(f) for batch in loader for f in batch]


@pytest.mark.parametrize("workers", [0, 2])
def test_ranks_draw_different_flips_and_a_rerun_draws_the_same(workers):
    rank0 = _flips(dp.rank_seed(42, 0), 0, workers)
    rank1 = _flips(dp.rank_seed(42, 1), 1, workers)
    assert rank0 != rank1
    assert rank0 == _flips(dp.rank_seed(42, 0), 0, workers)
    # Both directions: the same seed on every rank repeats the flips position by position.
    assert _flips(42, 0, workers) == _flips(42, 1, workers)


# --- the stem and the checkpoint keys -------------------------------------------

def test_sync_batchnorm_leaves_the_stem_and_the_checkpoint_keys_alone():
    model, _, _ = r3.build_backbone(9, "cpu", "imagenet")
    keys = set(model.state_dict())
    dp.sync_batchnorm(model)
    assert type(model.bn1) is nn.BatchNorm2d
    synced = [m for m in model.modules() if isinstance(m, nn.SyncBatchNorm)]
    plain = [m for m in model.modules() if type(m) is nn.BatchNorm2d]
    assert len(synced) == 52 and len(plain) == 1
    assert set(model.state_dict()) == keys
    assert r3.freeze_report(model)["stem"] == 0
    r3.stem_eval(model)
    assert not model.bn1.training and all(m.training for m in synced)
    # Both directions: converting the whole model would turn the stem's bn1 too.
    whole, _, _ = r3.build_backbone(9, "cpu", "imagenet")
    whole = nn.SyncBatchNorm.convert_sync_batchnorm(whole)
    assert isinstance(whole.bn1, nn.SyncBatchNorm)


# --- only rank 0 writes ------------------------------------------------------------

_WRITES = ("base.evidence", "torch.save", "tracking.log", "tracking.finish",
           "base.write_json", "manager.", "write_text", "r3.frame_predictions")


def _unguarded_writes(source):
    """Writing calls in ``finetune`` that are not under a ``main_rank`` condition."""
    tree = ast.parse(source)
    found = []

    def visit(node, guarded):
        if isinstance(node, (ast.If, ast.IfExp)) and "main_rank" in ast.unparse(node.test):
            for child in ast.iter_child_nodes(node):
                visit(child, guarded or child is not node.test)
            return
        if isinstance(node, ast.Call) and not guarded:
            text = ast.unparse(node.func)
            if any(text.startswith(w) or text.endswith(w) for w in _WRITES):
                found.append(text)
        for child in ast.iter_child_nodes(node):
            visit(child, guarded)

    visit(tree, False)
    return found


def test_evaluation_saving_and_records_are_rank_zeros_alone():
    source = inspect.getsource(dp.finetune)
    assert _unguarded_writes(source) == []
    # Both directions: a save moved out of the guard is caught.
    moved = source.replace("    dist.destroy_process_group()",
                           "    torch.save({}, 'x')\n    dist.destroy_process_group()")
    assert _unguarded_writes(moved) == ["torch.save"]


# --- the dispatch ---------------------------------------------------------------------

def _dispatch(monkeypatch, world):
    calls = []
    monkeypatch.setattr(r3.base, "deterministic", lambda seed: None)
    monkeypatch.setattr(r3.torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(r3, "finetune", lambda cfg: calls.append("one"))
    monkeypatch.setattr(dp, "finetune", lambda cfg: calls.append("several"))
    if world is None:
        monkeypatch.delenv("WORLD_SIZE", raising=False)
    else:
        monkeypatch.setenv("WORLD_SIZE", str(world))
    r3.main(OmegaConf.create({"seed": 42, "action": "finetune"}))
    return calls


def test_a_plain_launch_takes_the_one_gpu_path(monkeypatch):
    assert _dispatch(monkeypatch, None) == ["one"]
    assert _dispatch(monkeypatch, 1) == ["one"]
    # Both directions: a torchrun launch with two ranks takes the other path.
    assert _dispatch(monkeypatch, 2) == ["several"]


def test_only_the_fine_tune_runs_on_several_gpus(monkeypatch):
    monkeypatch.setattr(r3.base, "deterministic", lambda seed: None)
    monkeypatch.setattr(r3.torch.cuda, "is_available", lambda: True)
    monkeypatch.setenv("WORLD_SIZE", "2")
    with pytest.raises(ValueError):
        r3.main(OmegaConf.create({"seed": 42, "action": "extract"}))


# --- two GPUs: the same gradient as one -----------------------------------------------

def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _toy(seed):
    from torchvision.models import resnet18
    torch.manual_seed(seed)
    model = resnet18(num_classes=3)
    for module in (model.conv1, model.bn1):
        module.requires_grad_(False)
    return model


def _rank(rank, world, port, out, sync_bn):
    import os

    import torch.distributed as dist
    os.environ.update(MASTER_ADDR="127.0.0.1", MASTER_PORT=str(port))
    torch.backends.cudnn.allow_tf32 = torch.backends.cuda.matmul.allow_tf32 = False
    torch.cuda.set_device(rank)
    dist.init_process_group("nccl", rank=rank, world_size=world)
    device = torch.device("cuda", rank)
    generator = torch.Generator().manual_seed(1)
    images = torch.randn(10, 3, 64, 64, generator=generator).to(device)
    y = torch.randint(0, 3, (10,), generator=generator).to(device)
    batches = [list(range(6)), list(range(6, 10))]
    one = _toy(0).to(device)
    r3.stem_eval(one)
    for batch in batches:
        (nn.functional.cross_entropy(one(images[batch]), y[batch]) / 2).backward()
    model = _toy(0).to(device)
    ddp = dp.wrap(model, device, sync_bn=sync_bn)
    r3.stem_eval(model)
    for step, batch in enumerate(batches, start=1):
        part = dp.shard(batch, rank, world)
        dp.micro_step(ddp, images[part], y[part], len(batch), world, 2, step == 2)
    worst = max(float((a.grad - b.grad).norm() / a.grad.norm())
                for a, b in zip((p for p in one.parameters() if p.requires_grad),
                                (p for p in model.parameters() if p.requires_grad)))
    if rank == 0:
        Path(out).write_text(str(worst))
    dist.destroy_process_group()


def _relative_gradient_gap(tmp_path, sync_bn):
    out = tmp_path / f"gap_{sync_bn}.txt"
    torch.multiprocessing.spawn(_rank, args=(2, _free_port(), str(out), sync_bn), nprocs=2)
    return float(out.read_text())


@pytest.mark.skipif(not torch.cuda.is_available() or torch.cuda.device_count() < 2,
                    reason="needs two GPUs")
def test_two_gpus_give_the_one_gpu_gradient_over_an_uneven_tail(tmp_path):
    assert _relative_gradient_gap(tmp_path, True) < 1e-4
    # Both directions: without SyncBatchNorm each rank normalises its own shard.
    assert _relative_gradient_gap(tmp_path, False) > 1e-3
