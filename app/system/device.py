"""Hardware device selection (CPU vs CUDA) respecting the GTX 1650 4 GB limit."""

import shutil
import subprocess
from typing import Literal, Tuple
from app.system.limits import get_system_limits

DeviceType = Literal["auto", "cpu", "cuda"]


class DeviceManager:
    """Manages safe compute device assignment and VRAM verification."""

    @staticmethod
    def is_cuda_available() -> bool:
        """Determines if NVIDIA CUDA is available on the system."""
        try:
            import torch
            return bool(torch.cuda.is_available() and torch.cuda.device_count() > 0)
        except Exception:
            pass

        # Fallback check via nvidia-smi
        if shutil.which("nvidia-smi"):
            try:
                res = subprocess.run(["nvidia-smi"], capture_output=True, timeout=3)
                return res.returncode == 0
            except Exception:
                pass
        return False

    @staticmethod
    def get_vram_info_mb() -> Tuple[int, int]:
        """Returns (free_mb, total_mb) of primary GPU VRAM."""
        try:
            import torch
            if torch.cuda.is_available():
                free_b, total_b = torch.cuda.mem_get_info()
                return int(free_b / (1024 * 1024)), int(total_b / (1024 * 1024))
        except Exception:
            pass

        # Fallback query via nvidia-smi
        if shutil.which("nvidia-smi"):
            try:
                res = subprocess.run(
                    ["nvidia-smi", "--query-gpu=memory.free,memory.total", "--format=csv,nounits,noheader"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
                if res.returncode == 0:
                    lines = res.stdout.strip().splitlines()
                    if lines:
                        parts = [int(p.strip()) for p in lines[0].split(",")]
                        if len(parts) >= 2:
                            return parts[0], parts[1]
            except Exception:
                pass
        return 0, 0

    @classmethod
    def resolve_device(cls, requested: DeviceType = "auto") -> str:
        """Resolves requested device choice into 'cpu' or 'cuda' respecting safety limits."""
        limits = get_system_limits()

        if requested == "cpu":
            return "cpu"

        if requested == "cuda":
            if cls.is_cuda_available():
                return "cuda"
            return "cpu"

        # "auto" resolution
        if not limits.prefer_cuda_when_available or not cls.is_cuda_available():
            return "cpu"

        free_vram, total_vram = cls.get_vram_info_mb()
        # If free VRAM is below 1.2 GB, use CPU to avoid CUDA OOM on the 4 GB GTX 1650
        if total_vram > 0 and free_vram < 1200:
            return "cpu"

        return "cuda"
