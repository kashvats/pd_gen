"""Pronunciation Dictionary manager with instant phonetic testing and preview."""

from pathlib import Path
from typing import Optional, Dict
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QLineEdit,
    QHeaderView,
    QMessageBox,
    QTabWidget,
    QWidget,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from app.models.project import Project
from app.speech.pronunciation import PronunciationEngine
from app.tts.registry import tts_registry
from app.tts.base import SynthesisRequest, SynthesisResult


class PronunciationDialog(QDialog):
    """Pronunciation manager dialog for project and global replacement rules."""

    dictionary_changed = Signal()

    def __init__(self, project: Optional[Project] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pronunciation Dictionary — AI Voice Studio")
        self.setMinimumSize(620, 480)
        self.project = project

        self._player = QMediaPlayer(self)
        self._output = QAudioOutput(self)
        self._player.setAudioOutput(self._output)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel("📖 Pronunciation Dictionaries")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        layout.addWidget(header)

        # Tabs for Project vs Global
        self.tabs = QTabWidget()

        # Project Tab
        self.project_tab = QWidget()
        p_layout = QVBoxLayout(self.project_tab)
        self.project_table = self._create_table()
        p_layout.addWidget(self.project_table)
        self.tabs.addTab(self.project_tab, "This Project")

        # Global Tab
        self.global_tab = QWidget()
        g_layout = QVBoxLayout(self.global_tab)
        self.global_table = self._create_table()
        g_layout.addWidget(self.global_table)
        self.tabs.addTab(self.global_tab, "Global Defaults")

        layout.addWidget(self.tabs)

        # Add Entry Row
        add_group = QHBoxLayout()
        self.word_edit = QLineEdit()
        self.word_edit.setPlaceholderText("Original Word (e.g. OpenAI, Nguyen)")
        self.phonetic_edit = QLineEdit()
        self.phonetic_edit.setPlaceholderText("Pronunciation (e.g. Open A.I., Win)")

        self.add_btn = QPushButton("➕ Add / Update")
        self.add_btn.setObjectName("PrimaryButton")
        self.add_btn.clicked.connect(self._add_entry)

        add_group.addWidget(self.word_edit, 1)
        add_group.addWidget(self.phonetic_edit, 1)
        add_group.addWidget(self.add_btn)
        layout.addLayout(add_group)

        # Action Buttons Row
        actions = QHBoxLayout()
        self.preview_btn = QPushButton("▶ Test Pronunciation")
        self.preview_btn.clicked.connect(self._preview_word)

        self.remove_btn = QPushButton("🗑 Remove Selected")
        self.remove_btn.clicked.connect(self._remove_entry)

        self.save_close_btn = QPushButton("Save & Close")
        self.save_close_btn.setObjectName("PrimaryButton")
        self.save_close_btn.clicked.connect(self._save_and_close)

        actions.addWidget(self.preview_btn)
        actions.addWidget(self.remove_btn)
        actions.addStretch(1)
        actions.addWidget(self.save_close_btn)
        layout.addLayout(actions)

        self._populate_tables()

    def _create_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Original Word / Phrase", "Spoken Replacement"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        return table

    def _populate_tables(self):
        # Project Dict
        proj_dict = self.project.pronunciation_dictionary if self.project else {}
        self.project_table.setRowCount(len(proj_dict))
        for row, (k, v) in enumerate(proj_dict.items()):
            self.project_table.setItem(row, 0, QTableWidgetItem(k))
            self.project_table.setItem(row, 1, QTableWidgetItem(v))

        # Global Dict
        global_dict = PronunciationEngine.load_global_dict()
        self.global_table.setRowCount(len(global_dict))
        for row, (k, v) in enumerate(global_dict.items()):
            self.global_table.setItem(row, 0, QTableWidgetItem(k))
            self.global_table.setItem(row, 1, QTableWidgetItem(v))

    def _add_entry(self):
        word = self.word_edit.text().strip()
        phonetic = self.phonetic_edit.text().strip()
        if not word or not phonetic:
            return

        is_global = (self.tabs.currentIndex() == 1)
        if is_global:
            g_dict = PronunciationEngine.load_global_dict()
            g_dict[word] = phonetic
            PronunciationEngine.save_global_dict(g_dict)
        else:
            if self.project:
                self.project.pronunciation_dictionary[word] = phonetic

        self._populate_tables()
        self.word_edit.clear()
        self.phonetic_edit.clear()

    def _remove_entry(self):
        is_global = (self.tabs.currentIndex() == 1)
        table = self.global_table if is_global else self.project_table
        sel = table.selectedItems()
        if not sel:
            return
        row = sel[0].row()
        word = table.item(row, 0).text()

        if is_global:
            g_dict = PronunciationEngine.load_global_dict()
            if word in g_dict:
                del g_dict[word]
                PronunciationEngine.save_global_dict(g_dict)
        else:
            if self.project and word in self.project.pronunciation_dictionary:
                del self.project.pronunciation_dictionary[word]

        self._populate_tables()

    def _preview_word(self):
        word = self.phonetic_edit.text().strip() or self.word_edit.text().strip()
        if not word:
            table = self.global_table if self.tabs.currentIndex() == 1 else self.project_table
            sel = table.selectedItems()
            if sel:
                row = sel[0].row()
                word = table.item(row, 1).text()

        if not word:
            return

        provider = tts_registry.get("elevenlabs") or tts_registry.get("mock")
        if not provider or not provider.is_configured():
            provider = tts_registry.get("mock")

        try:
            req = SynthesisRequest(
                text=word,
                voice_id="default",
                provider=provider.provider_id,
                studio_mode=True,
            )
            res: SynthesisResult = provider.synthesize(req)
            temp_f = Path("data/cache/pronounce_temp.wav")
            temp_f.parent.mkdir(parents=True, exist_ok=True)
            temp_f.write_bytes(res.audio_bytes)
            self._player.setSource(QUrl.fromLocalFile(str(temp_f.resolve())))
            self._player.play()
        except Exception:
            pass

    def _save_and_close(self):
        self.dictionary_changed.emit()
        self.accept()
