"""Hardware limits, performance profiles, and concurrency bounds."""

from dataclasses import dataclass
from typing import Literal

PerformanceProfile = Literal["safe", "balanced", "performance"]


@dataclass
class SystemLimits:
    """Hardware bounds and concurrency rules for the target system."""
    profile: PerformanceProfile = "balanced"
    max_heavy_synthesis_concurrency: int = 1
    max_ffmpeg_concurrency: int = 1
    cpu_thread_budget: int = 6
    max_vram_target_mb: int = 3200  # Conservative soft cap for 4GB GTX 1650
    min_free_disk_reserve_gb: float = 10.0
    max_cache_budget_gb: float = 20.0
    prefer_cuda_when_available: bool = True

    @classmethod
    def create(cls, profile: PerformanceProfile = "balanced") -> "SystemLimits":
        if profile == "safe":
            return cls(
                profile="safe",
                max_heavy_synthesis_concurrency=1,
                max_ffmpeg_concurrency=1,
                cpu_thread_budget=4,
                max_vram_target_mb=2400,
                prefer_cuda_when_available=False,
            )
        elif profile == "performance":
            return cls(
                profile="performance",
                max_heavy_synthesis_concurrency=1,
                max_ffmpeg_concurrency=1,
                cpu_thread_budget=8,
                max_vram_target_mb=3200,
                prefer_cuda_when_available=True,
            )
        else:  # balanced
            return cls(
                profile="balanced",
                max_heavy_synthesis_concurrency=1,
                max_ffmpeg_concurrency=1,
                cpu_thread_budget=6,
                max_vram_target_mb=3000,
                prefer_cuda_when_available=True,
            )


# Global singleton limits instance
_CURRENT_LIMITS = SystemLimits.create("balanced")


def get_system_limits() -> SystemLimits:
    return _CURRENT_LIMITS


def set_system_profile(profile: PerformanceProfile) -> SystemLimits:
    global _CURRENT_LIMITS
    _CURRENT_LIMITS = SystemLimits.create(profile)
    return _CURRENT_LIMITS
