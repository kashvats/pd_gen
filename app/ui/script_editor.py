"""Dual-mode Script Editor supporting raw Markdown and interactive Dialogue Turn cards."""

from pathlib import Path
from typing import Optional, List, Dict
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QPlainTextEdit,
    QScrollArea,
    QFrame,
    QLabel,
    QPushButton,
    QComboBox,
    QCheckBox,
    QSizePolicy,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from app.models.project import Project
from app.models.ast import DialogueNode
from app.models.generation import SegmentGenerationInfo, Take
from app.audio.takes import TakeManager


class TurnCard(QFrame):
    """Interactive card for a single dialogue turn with takes and locking."""

    preview_requested = Signal(str)      # audio_path
    new_take_requested = Signal(str)     # segment_id
    lock_toggled = Signal(str, bool)     # segment_id, is_locked
    take_changed = Signal(str, int)      # segment_id, take_index

    def __init__(self, node: DialogueNode, gen_info: Optional[SegmentGenerationInfo], parent=None):
        super().__init__(parent)
        self.node = node
        self.gen_info = gen_info
        self._init_ui()

    def _init_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            TurnCard {
                background-color: #1A1A20;
                border: 1px solid #2E2E38;
                border-radius: 8px;
                padding: 10px;
                margin-bottom: 8px;
            }
            TurnCard:hover {
                border-color: #4F46E5;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # Header Row: Speaker Name Badge, Status Badge, Inferred Direction
        header = QHBoxLayout()
        self.speaker_badge = QLabel(f"  {self.node.speaker.upper()}  ")
        self.speaker_badge.setStyleSheet("""
            background-color: #312E81;
            color: #C7D2FE;
            font-weight: bold;
            font-size: 11px;
            border-radius: 4px;
            padding: 3px 6px;
        """)

        self.status_badge = QLabel(self._get_status_text())
        self.status_badge.setStyleSheet(self._get_status_style())

        self.direction_badge = QLabel(self._get_direction_text())
        self.direction_badge.setStyleSheet("color: #94A3B8; font-style: italic; font-size: 11px;")

        header.addWidget(self.speaker_badge)
        header.addWidget(self.status_badge)
        header.addWidget(self.direction_badge, 1)
        layout.addLayout(header)

        # Dialogue Text
        self.text_label = QLabel(self.node.text)
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet("color: #F1F5F9; font-size: 13px; line-height: 1.4;")
        layout.addWidget(self.text_label)

        # Actions & Takes Footer Row
        footer = QHBoxLayout()
        footer.setSpacing(8)

        self.preview_btn = QPushButton("▶ Preview")
        self.preview_btn.setFixedHeight(26)
        self.preview_btn.setToolTip("Preview audio for this turn")
        self.preview_btn.clicked.connect(self._on_preview_clicked)

        self.take_combo = QComboBox()
        self.take_combo.setFixedHeight(26)
        self._populate_takes()
        self.take_combo.currentIndexChanged.connect(self._on_take_selected)

        self.lock_btn = QPushButton("🔓 Unlock")
        self.lock_btn.setFixedHeight(26)
        self._update_lock_btn()
        self.lock_btn.clicked.connect(self._on_lock_clicked)

        self.new_take_btn = QPushButton("🔄 New Take")
        self.new_take_btn.setFixedHeight(26)
        self.new_take_btn.setToolTip("Generate another alternate take for this line")
        self.new_take_btn.clicked.connect(lambda: self.new_take_requested.emit(self.node.id))

        footer.addWidget(self.preview_btn)
        footer.addWidget(QLabel("Take:"))
        footer.addWidget(self.take_combo)
        footer.addWidget(self.lock_btn)
        footer.addWidget(self.new_take_btn)
        footer.addStretch(1)

        layout.addLayout(footer)

    def _get_status_text(self) -> str:
        if not self.gen_info:
            return "Waiting"
        st = self.gen_info.status
        return st.capitalize()

    def _get_status_style(self) -> str:
        st = self.gen_info.status if self.gen_info else "waiting"
        color_map = {
            "complete": "color: #10B981; font-weight: 600;",
            "cached": "color: #06B6D4; font-weight: 600;",
            "locked": "color: #F59E0B; font-weight: 600;",
            "generating": "color: #818CF8; font-weight: 600;",
            "failed": "color: #EF4444; font-weight: 600;",
            "waiting": "color: #64748B; font-weight: 600;",
        }
        return color_map.get(st, "color: #64748B;")

    def _get_direction_text(self) -> str:
        if self.gen_info and self.gen_info.inferred_direction:
            dir_text = self.gen_info.inferred_direction
            if len(dir_text) > 65:
                dir_text = dir_text[:62] + "..."
            return f"Direction: {dir_text}"
        return ""

    def _populate_takes(self):
        self.take_combo.blockSignals(True)
        self.take_combo.clear()
        if self.gen_info and self.gen_info.takes:
            for idx, t in enumerate(self.gen_info.takes, start=1):
                lock_str = " 🔒" if t.is_locked else ""
                self.take_combo.addItem(f"Take {idx}{lock_str}", idx - 1)
            self.take_combo.setCurrentIndex(self.gen_info.active_take_index)
            self.preview_btn.setEnabled(True)
        else:
            self.take_combo.addItem("No takes yet", 0)
            self.preview_btn.setEnabled(False)
        self.take_combo.blockSignals(False)

    def _update_lock_btn(self):
        is_locked = self.gen_info.is_locked if self.gen_info else False
        if is_locked:
            self.lock_btn.setText("🔒 Locked")
            self.lock_btn.setStyleSheet("background-color: #78350F; color: #FDE68A;")
        else:
            self.lock_btn.setText("🔓 Unlocked")
            self.lock_btn.setStyleSheet("")

    def _on_preview_clicked(self):
        if self.gen_info and self.gen_info.active_take:
            path = self.gen_info.active_take.audio_path
            if path and Path(path).exists():
                self.preview_requested.emit(path)

    def _on_lock_clicked(self):
        if self.gen_info:
            new_state = TakeManager.toggle_lock_active_take(self.gen_info)
            self._update_lock_btn()
            self._populate_takes()
            self.status_badge.setText(self._get_status_text())
            self.status_badge.setStyleSheet(self._get_status_style())
            self.lock_toggled.emit(self.node.id, new_state)

    def _on_take_selected(self, index: int):
        if self.gen_info and 0 <= index < len(self.gen_info.takes):
            TakeManager.set_active_take(self.gen_info, index)
            self._update_lock_btn()
            self.status_badge.setText(self._get_status_text())
            self.status_badge.setStyleSheet(self._get_status_style())
            self.take_changed.emit(self.node.id, index)


class ScriptEditorWidget(QWidget):
    """Dual-view widget with raw Markdown and structured Dialogue Turn cards."""

    take_selection_modified = Signal()
    markdown_modified = Signal(str)
    single_turn_generate_requested = Signal(str, bool)  # segment_id, force_new_take

    def __init__(self, parent=None):
        super().__init__(parent)
        self._project: Optional[Project] = None

        self._single_player = QMediaPlayer(self)
        self._single_output = QAudioOutput(self)
        self._single_player.setAudioOutput(self._single_output)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()

        # Tab 1: Structured Dialogue Cards
        self.cards_scroll = QScrollArea()
        self.cards_scroll.setWidgetResizable(True)
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(8, 8, 8, 8)
        self.cards_layout.setSpacing(6)
        self.cards_layout.addStretch(1)
        self.cards_scroll.setWidget(self.cards_container)

        # Tab 2: Raw Markdown Editor
        self.md_editor = QPlainTextEdit()
        self.md_editor.setPlaceholderText("Write or paste your Markdown script here...\n\nHost: Welcome back!\nCo-Host: Thanks!")
        self.md_editor.setStyleSheet("font-family: monospace; font-size: 13px; background-color: #0E0E12;")
        self.md_editor.textChanged.connect(self._on_markdown_text_changed)

        self.tabs.addTab(self.cards_scroll, "🎙 Dialogue Studio Cards")
        self.tabs.addTab(self.md_editor, "📝 Raw Markdown Source")

        layout.addWidget(self.tabs)

    def load_project(self, project: Project):
        """Populates the script editor with the project content."""
        self._project = project
        self.md_editor.blockSignals(True)
        self.md_editor.setPlainText(project.markdown)
        self.md_editor.blockSignals(False)
        self.refresh_cards()

    def refresh_cards(self):
        """Re-renders the dialogue turn cards according to parsed nodes."""
        if not self._project:
            return

        # Clear existing card widgets
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for node_dict in self._project.script_nodes:
            if node_dict.get("type") == "dialogue":
                node = DialogueNode.from_dict(node_dict)
                gen_info = self._project.segments_generation.get(node.id)
                card = TurnCard(node, gen_info)

                card.preview_requested.connect(self._play_card_audio)
                card.new_take_requested.connect(lambda sid: self.single_turn_generate_requested.emit(sid, True))
                card.lock_toggled.connect(self._on_card_lock_toggled)
                card.take_changed.connect(self._on_card_take_changed)

                self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

    def _play_card_audio(self, audio_path: str):
        if audio_path and Path(audio_path).exists():
            self._single_player.setSource(QUrl.fromLocalFile(audio_path))
            self._single_player.play()

    def _on_markdown_text_changed(self):
        text = self.md_editor.toPlainText()
        self.markdown_modified.emit(text)

    def _on_card_lock_toggled(self, segment_id: str, is_locked: bool):
        self.take_selection_modified.emit()

    def _on_card_take_changed(self, segment_id: str, take_index: int):
        self.take_selection_modified.emit()
