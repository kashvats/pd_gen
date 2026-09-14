"""Read-only installation guidance. No paid-provider setup in the free studio."""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from app.tts.registry import tts_registry
from app.config.settings import Settings


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Speech engine setup")
        self.setMinimumWidth(560)
        layout = QVBoxLayout(self)
        ready = tts_registry.get("kokoro").is_configured()
        label = QLabel(
            f"Kokoro offline neural voices: {'model files found' if ready else 'installation required'}\n\n"
            "One-time setup (internet required for installation):\n"
            "python -m pip install -r requirements.txt\n"
            "python scripts/install_kokoro.py --download\n\n"
            "About 340 MB of model files. Runs on CPU; no API key.\n"
            "Once installed, Kokoro generates speech offline.\n\n"
            f"FFmpeg: {'found' if Settings.find_ffmpeg() else 'missing — install before exporting'}\n"
            f"ffprobe: {'found' if Settings.find_ffprobe() else 'missing — install before exporting'}\n\n"
            "Edge is optional and sends script text to Microsoft.\n"
            "Voice quality depends on the voice, language, and script.\n"
            "These engines do not follow free-form emotion/acting prompts.\n"
            "Legacy fake cloning is disabled; saved reference files remain intact."
        )
        label.setWordWrap(True)
        layout.addWidget(label)
        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        layout.addWidget(close)
