"""Tests for system limits, device resolution, and safe cache pruning."""

import pytest
import tempfile
from pathlib import Path
from app.system.limits import get_system_limits, set_system_profile, SystemLimits
from app.system.device import DeviceManager
from app.system.resources import SystemResourceManager, SystemSnapshot


def test_performance_profiles():
    safe = set_system_profile("safe")
    assert safe.profile == "safe"
    assert safe.cpu_thread_budget == 4
    assert safe.max_heavy_synthesis_concurrency == 1

    perf = set_system_profile("performance")
    assert perf.profile == "performance"
    assert perf.cpu_thread_budget == 8

    bal = set_system_profile("balanced")
    assert bal.profile == "balanced"
    assert bal.cpu_thread_budget == 6


def test_device_manager_resolution():
    cpu_res = DeviceManager.resolve_device("cpu")
    assert cpu_res == "cpu"

    auto_res = DeviceManager.resolve_device("auto")
    assert auto_res in ["cpu", "cuda"]


def test_system_resource_snapshot():
    snap: SystemSnapshot = SystemResourceManager.get_snapshot()
    assert snap.ram_total_gb > 0
    assert snap.free_disk_gb >= 0
    assert snap.is_disk_safe is True
    assert snap.is_memory_safe is True


def test_safe_cache_pruning_never_touches_user_data():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Create dummy cache files
        for i in range(5):
            (cache_dir / f"hash_{i}.wav").write_bytes(b"0" * 1024 * 1024)

        # Budget of 2 MB should prune older files down to budget
        removed = SystemResourceManager.prune_cache_safely(max_budget_gb=0.002, cache_dir=cache_dir)
        assert removed > 0

