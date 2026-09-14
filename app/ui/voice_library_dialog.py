"""Voice Library dialog for browsing, testing, and managing saved and cloned voices."""

from pathlib import Path
from typing import Optional, List
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QHeaderView,
    QMessageBox,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from app.models.voice import VoiceProfile
from app.voices.library import VoiceLibrary
from app.ui.voice_cloning_dialog import VoiceCloningDialog
from app.tts.registry import tts_registry
from app.tts.base import SynthesisRequest, SynthesisResult


class VoiceLibraryDialog(QDialog):
    """Local Voice Library manager dialog."""

    library_updated = Signal()

    def __init__(self, voice_library: Optional[VoiceLibrary] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Voice Library — AI Voice Studio")
        self.setMinimumSize(720, 480)
        self.voice_library = voice_library or VoiceLibrary()

        self._preview_player = QMediaPlayer(self)
        self._preview_output = QAudioOutput(self)
        self._preview_player.setAudioOutput(self._preview_output)

        self._init_ui()
        self.refresh_table()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header_row = QHBoxLayout()
        title = QLabel("📚 Voice Library")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        header_row.addWidget(title)
        header_row.addStretch(1)

        self.clone_btn = QPushButton("✨ Clone New Voice...")
        self.clone_btn.setObjectName("PrimaryButton")
        self.clone_btn.setEnabled(False)
        self.clone_btn.setText("Cloning model not installed")
        self.clone_btn.setToolTip("The old cloning adapter generated tones. Saved references remain available.")
        self.clone_btn.clicked.connect(self._open_cloning_wizard)
        header_row.addWidget(self.clone_btn)
        layout.addLayout(header_row)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Name", "Provider", "Type", "Voice ID", "Description"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.table)

        # Bottom Actions
        actions_row = QHBoxLayout()
        self.preview_btn = QPushButton("▶ Preview Selected Voice")
        self.preview_btn.clicked.connect(self._preview_selected)

        self.delete_btn = QPushButton("🗑 Delete Voice")
        self.delete_btn.clicked.connect(self._delete_selected)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)

        actions_row.addWidget(self.preview_btn)
        actions_row.addWidget(self.delete_btn)
        actions_row.addStretch(1)
        actions_row.addWidget(self.close_btn)
        layout.addLayout(actions_row)

    def refresh_table(self):
        self.table.setRowCount(0)
        voices = self.voice_library.list_voices()
        self.table.setRowCount(len(voices))

        for row, v in enumerate(voices):
            self.table.setItem(row, 0, QTableWidgetItem(v.name))
            self.table.setItem(row, 1, QTableWidgetItem(v.provider.capitalize()))
            v_type = "Cloned" if "clone" in v.voice_type else "Preset"
            self.table.setItem(row, 2, QTableWidgetItem(v_type))
            self.table.setItem(row, 3, QTableWidgetItem(v.voice_id))
            self.table.setItem(row, 4, QTableWidgetItem(v.description or ""))
            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, v.id)

    def _open_cloning_wizard(self):
        dlg = VoiceCloningDialog(self.voice_library, self)
        dlg.voice_cloned.connect(self._on_voice_cloned)
        dlg.exec()

    def _on_voice_cloned(self):
        self.refresh_table()
        self.library_updated.emit()

    def _get_selected_voice(self) -> Optional[VoiceProfile]:
        sel = self.table.selectedItems()
        if not sel:
            return None
        row = sel[0].row()
        item = self.table.item(row, 0)
        if item:
            voice_id = item.data(Qt.ItemDataRole.UserRole)
            return self.voice_library.get_voice(voice_id)
        return None

    def _preview_selected(self):
        voice = self._get_selected_voice()
        if not voice:
            QMessageBox.information(self, "No Selection", "Please select a voice from the table.")
            return

        provider = tts_registry.get(voice.provider)
        if not provider or provider.category == "DISABLED":
            QMessageBox.warning(self, "Unavailable", "Select an installed neural voice.")
            return
        allowed = False
        if not provider.capabilities.local:
            allowed = QMessageBox.question(self, "Online preview", "Send this preview text to Microsoft?") == QMessageBox.StandardButton.Yes
            if not allowed:
                return
        from app.ui.task_worker import TaskWorker
        req = SynthesisRequest(text="That's interesting. Could you explain how it works?",
            voice_id=voice.voice_id, provider=provider.provider_id,
            speed=voice.delivery.pace, settings={"allow_online": allowed})
        def task():
            import uuid
            result = provider.synthesize(req)
            path = Path(self.voice_library.root_dir) / f"preview_{uuid.uuid4().hex}.{result.audio_format}"
            path.write_bytes(result.audio_bytes)
            return str(path)
        self.preview_btn.setEnabled(False)
        self._worker = TaskWorker(task, self)
        self._worker.result_ready.connect(self._play_result)
        self._worker.failed.connect(lambda message: QMessageBox.warning(self, "Preview failed", message))
        self._worker.finished.connect(lambda: self.preview_btn.setEnabled(True))
        self._worker.start()

    def _play_result(self, path):
        self._preview_player.setSource(QUrl.fromLocalFile(path))
        self._preview_player.play()

    def done(self, result):
        if hasattr(self, "_worker") and self._worker.isRunning():
            QMessageBox.information(self, "Preview running", "Wait for the current preview to finish.")
            return
        super().done(result)

    def _delete_selected(self):
        voice = self._get_selected_voice()
        if not voice:
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete voice profile '{voice.name}'?",
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.voice_library.delete_voice(voice.id)
            self.refresh_table()
            self.library_updated.emit()
