"""Application settings, environment variables, and filesystem paths."""

import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

# Base paths
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
VOICES_DIR = DATA_DIR / "voices"
CACHE_DIR = DATA_DIR / "cache"
PROJECTS_DIR = DATA_DIR / "projects"
CONFIG_DIR = DATA_DIR / "config"
GLOBAL_PRONUNCIATION_FILE = CONFIG_DIR / "pronunciation.json"
GLOBAL_CHARACTERS_FILE = CONFIG_DIR / "characters.json"

# Ensure runtime directories exist
for directory in [DATA_DIR, VOICES_DIR, CACHE_DIR, PROJECTS_DIR, CONFIG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Load .env file
ENV_FILE = ROOT_DIR / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv()


class Settings:
    """Settings manager for local studio environment."""

    @staticmethod
    def get_api_key(provider: str) -> str:
        env_map = {
            "elevenlabs": "ELEVENLABS_API_KEY",
            "cartesia": "CARTESIA_API_KEY",
            "openai": "OPENAI_API_KEY",
        }
        var_name = env_map.get(provider.lower(), f"{provider.upper()}_API_KEY")
        return os.environ.get(var_name, "").strip()

    @staticmethod
    def set_api_key(provider: str, key: str) -> None:
        env_map = {
            "elevenlabs": "ELEVENLABS_API_KEY",
            "cartesia": "CARTESIA_API_KEY",
            "openai": "OPENAI_API_KEY",
        }
        var_name = env_map.get(provider.lower(), f"{provider.upper()}_API_KEY")
        os.environ[var_name] = key.strip()
        Settings.save_env({var_name: key.strip()})

    @staticmethod
    def save_env(updates: dict[str, str]) -> None:
        """Persist environment key-value pairs to .env."""
        existing_lines = []
        if ENV_FILE.exists():
            existing_lines = ENV_FILE.read_text(encoding="utf-8").splitlines()

        current_vars = {}
        order = []
        for line in existing_lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" in stripped:
                k, v = stripped.split("=", 1)
                k = k.strip()
                v = v.strip()
                current_vars[k] = v
                if k not in order:
                    order.append(k)

        for k, v in updates.items():
            current_vars[k] = v
            if k not in order:
                order.append(k)

        out_lines = ["# TTS Provider API Keys (Local use only)"]
        for k in order:
            out_lines.append(f"{k}={current_vars[k]}")

        ENV_FILE.write_text("\n".join(out_lines) + "\n", encoding="utf-8")

    @staticmethod
    def find_ffmpeg() -> str | None:
        """Locate ffmpeg binary in system PATH or custom setting."""
        custom_path = os.environ.get("FFMPEG_PATH")
        if custom_path and Path(custom_path).exists():
            return custom_path
        which_path = shutil.which("ffmpeg")
        return which_path

    @staticmethod
    def find_ffprobe() -> str | None:
        """Locate ffprobe binary in system PATH or custom setting."""
        custom_path = os.environ.get("FFPROBE_PATH")
        if custom_path and Path(custom_path).exists():
            return custom_path
        which_path = shutil.which("ffprobe")
        return which_path
