"""Cast & Voice Assignment Panel for character direction and voice configuration."""

from pathlib import Path
from typing import Optional, Dict, List
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QGroupBox,
    QLabel,
    QPushButton,
    QComboBox,
    QSlider,
    QTextEdit,
    QFrame,
    QMessageBox,
    QSizePolicy,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from app.models.project import Project, SpeakerProfile
from app.models.voice import VoiceProfile, VoiceDelivery
from app.speech.presets import QUALITY_PRESETS
from app.voices.library import VoiceLibrary
from app.tts.registry import tts_registry
from app.tts.base import SynthesisRequest, SynthesisResult


class SpeakerCard(QGroupBox):
    """Configuration panel for an individual character."""

    voice_changed = Signal(str)

    def __init__(
        self,
        speaker_name: str,
        profile: SpeakerProfile,
        voice_library: VoiceLibrary,
        parent=None,
    ):
        super().__init__(f"Speaker: {speaker_name}", parent)
        self.speaker_name = speaker_name
        self.profile = profile
        self.voice_library = voice_library

        self._preview_player = QMediaPlayer(self)
        self._preview_output = QAudioOutput(self)
        self._preview_player.setAudioOutput(self._preview_output)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 14, 12, 12)
        layout.setSpacing(10)

        # Voice Selector & Preview Row
        voice_row = QHBoxLayout()
        self.voice_combo = QComboBox()
        self.voice_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.voice_combo.setMinimumContentsLength(16)
        self.voice_combo.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self._populate_voices()
        self.voice_combo.currentIndexChanged.connect(self._on_voice_selected)

        self.preview_voice_btn = QPushButton("▶ Test Voice")
        self.preview_voice_btn.setFixedHeight(28)
        self.preview_voice_btn.clicked.connect(self._preview_voice)

        voice_row.addWidget(QLabel("Voice:"))
        voice_row.addWidget(self.voice_combo, 1)
        voice_row.addWidget(self.preview_voice_btn)
        layout.addLayout(voice_row)

        # Preset Selector Row
        preset_row = QHBoxLayout()
        self.preset_combo = QComboBox()
        for p_name in QUALITY_PRESETS.keys():
            self.preset_combo.addItem(p_name)
        self.preset_combo.setCurrentText(self.profile.preset or "Natural Conversation")
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)

        preset_row.addWidget(QLabel("Style Preset:"))
        preset_row.addWidget(self.preset_combo, 1)
        layout.addLayout(preset_row)

        # Direction Prompt
        layout.addWidget(QLabel("Character Direction / Acting Prompt:"))
        self.direction_edit = QTextEdit()
        self.direction_edit.setPlaceholderText("e.g. Warm, confident podcast host. Natural, subtle pacing.")
        self.direction_edit.setPlainText(self.profile.direction_prompt)
        self.direction_edit.setFixedHeight(50)
        self.direction_edit.textChanged.connect(self._on_direction_changed)
        layout.addWidget(self.direction_edit)

        # Sliders Grid (Pace, Energy, Expressiveness, Warmth)
        sliders_frame = QFrame()
        sliders_layout = QVBoxLayout(sliders_frame)
        sliders_layout.setContentsMargins(0, 0, 0, 0)
        sliders_layout.setSpacing(6)

        # Pace Slider (0.7x to 1.3x)
        self.pace_label = QLabel(f"Pace: {self.profile.delivery.pace:.2f}x")
        self.pace_slider = QSlider(Qt.Orientation.Horizontal)
        self.pace_slider.setRange(70, 130)
        self.pace_slider.setValue(int(self.profile.delivery.pace * 100))
        self.pace_slider.valueChanged.connect(self._on_pace_changed)

        # Energy Slider
        self.energy_label = QLabel(f"Energy: {int(self.profile.delivery.energy * 100)}%")
        self.energy_slider = QSlider(Qt.Orientation.Horizontal)
        self.energy_slider.setRange(0, 100)
        self.energy_slider.setValue(int(self.profile.delivery.energy * 100))
        self.energy_slider.valueChanged.connect(self._on_energy_changed)

        # Expressiveness Slider
        self.expr_label = QLabel(f"Expressiveness: {int(self.profile.delivery.expressiveness * 100)}%")
        self.expr_slider = QSlider(Qt.Orientation.Horizontal)
        self.expr_slider.setRange(0, 100)
        self.expr_slider.setValue(int(self.profile.delivery.expressiveness * 100))
        self.expr_slider.valueChanged.connect(self._on_expr_changed)

        # Warmth Slider
        self.warmth_label = QLabel(f"Warmth: {int(self.profile.delivery.warmth * 100)}%")
        self.warmth_slider = QSlider(Qt.Orientation.Horizontal)
        self.warmth_slider.setRange(0, 100)
        self.warmth_slider.setValue(int(self.profile.delivery.warmth * 100))
        self.warmth_slider.valueChanged.connect(self._on_warmth_changed)

        p_row = QHBoxLayout()
        p_row.addWidget(self.pace_label)
        p_row.addWidget(self.pace_slider)

        e_row = QHBoxLayout()
        e_row.addWidget(self.energy_label)
        e_row.addWidget(self.energy_slider)

        ex_row = QHBoxLayout()
        ex_row.addWidget(self.expr_label)
        ex_row.addWidget(self.expr_slider)

        w_row = QHBoxLayout()
        w_row.addWidget(self.warmth_label)
        w_row.addWidget(self.warmth_slider)

        sliders_layout.addLayout(p_row)
        sliders_layout.addLayout(e_row)
        sliders_layout.addLayout(ex_row)
        sliders_layout.addLayout(w_row)

        layout.addWidget(sliders_frame)
        self.capability_label = QLabel()
        self.capability_label.setWordWrap(True)
        self.capability_label.setMinimumWidth(0)
        self.capability_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.capability_label)
        self._update_capabilities()

    def _update_capabilities(self):
        provider = tts_registry.get(self.profile.provider)
        capable = bool(provider and provider.capabilities.style_instructions)
        for control in (self.direction_edit, self.energy_slider, self.expr_slider, self.warmth_slider):
            control.setEnabled(capable)
        self.capability_label.setText("Voice and pace control the sound. Acting/emotion prompts are unsupported "
                                      "by this engine." if not capable else "Acting prompts supported.")

    def _populate_voices(self):
        self.voice_combo.blockSignals(True)
        self.voice_combo.clear()

        # Add library voices
        library_voices = self.voice_library.list_voices()
        for v in library_voices:
            provider = tts_registry.get(v.provider)
            if not provider or provider.category == "DISABLED":
                continue
            clone_mark = " (Clone)" if "clone" in v.voice_type else ""
            label = f"{v.name} [{v.provider.capitalize()}]{clone_mark}"
            self.voice_combo.addItem(label, v.to_dict())

        # Select currently configured voice
        selected_idx = -1
        for i in range(self.voice_combo.count()):
            v_data = self.voice_combo.itemData(i)
            if v_data and v_data.get("voice_id") == self.profile.voice_id and v_data.get("provider") == self.profile.provider:
                selected_idx = i
                break
        self.voice_combo.setCurrentIndex(selected_idx)
        self.voice_combo.blockSignals(False)

    def _on_voice_selected(self, idx: int):
        v_data = self.voice_combo.itemData(idx)
        if v_data:
            self.profile.voice_name = v_data.get("name", "")
            self.profile.provider = v_data.get("provider", "edge_tts")
            self.profile.voice_id = v_data.get("voice_id", "")
            self.profile.voice_type = v_data.get("voice_type", "builtin")
            self.profile.settings = dict(v_data.get("settings", {}))
            self._update_capabilities()
            self.voice_changed.emit(self.speaker_name)

    def _on_preset_changed(self, preset_name: str):
        self.profile.preset = preset_name
        preset_data = QUALITY_PRESETS.get(preset_name)
        if preset_data:
            deliv = preset_data.delivery
            self.profile.delivery = VoiceDelivery(
                pace=deliv.pace,
                energy=deliv.energy,
                expressiveness=deliv.expressiveness,
                warmth=deliv.warmth,
            )
            # Update UI sliders
            self.pace_slider.blockSignals(True)
            self.pace_slider.setValue(int(deliv.pace * 100))
            self.pace_label.setText(f"Pace: {deliv.pace:.2f}x")
            self.pace_slider.blockSignals(False)
            self.voice_changed.emit(self.speaker_name)

    def _on_direction_changed(self):
        self.profile.direction_prompt = self.direction_edit.toPlainText()
        self.voice_changed.emit(self.speaker_name)

    def _on_pace_changed(self, val: int):
        pace = val / 100.0
        self.profile.delivery.pace = pace
        self.pace_label.setText(f"Pace: {pace:.2f}x")
        self.voice_changed.emit(self.speaker_name)

    def _on_energy_changed(self, val: int):
        energy = val / 100.0
        self.profile.delivery.energy = energy
        self.energy_label.setText(f"Energy: {val}%")

    def _on_expr_changed(self, val: int):
        expr = val / 100.0
        self.profile.delivery.expressiveness = expr
        self.expr_label.setText(f"Expressiveness: {val}%")

    def _on_warmth_changed(self, val: int):
        warmth = val / 100.0
        self.profile.delivery.warmth = warmth
        self.warmth_label.setText(f"Warmth: {val}%")

    def _preview_voice(self):
        provider = tts_registry.get(self.profile.provider)
        if not provider or provider.category == "DISABLED":
            QMessageBox.warning(self, "Voice unavailable", "Select a Kokoro or Edge neural voice.")
            return
        allow_online = False
        if not provider.capabilities.local:
            allow_online = QMessageBox.question(self, "Online voice preview",
                "Send this short preview text to Microsoft to generate speech?") == QMessageBox.StandardButton.Yes
            if not allow_online:
                return
        from app.ui.task_worker import TaskWorker
        req = SynthesisRequest(text=f"Hello, I am {self.speaker_name}. Welcome to the show.",
            voice_id=self.profile.voice_id, provider=provider.provider_id,
            speed=self.profile.delivery.pace, settings={"allow_online": allow_online})
        def task():
            import uuid
            result = provider.synthesize(req)
            path = Path(self.voice_library.root_dir) / f"preview_{uuid.uuid4().hex}.{result.audio_format}"
            path.write_bytes(result.audio_bytes)
            return str(path)
        self.preview_voice_btn.setEnabled(False)
        # Parent worker to the window so editing a script cannot destroy a running thread.
        self._preview_worker = TaskWorker(task, self.window())
        self._preview_worker.result_ready.connect(self._play_preview)
        self._preview_worker.failed.connect(self._preview_error)
        self._preview_worker.finished.connect(self._preview_finished)
        self._preview_worker.start()

    def _preview_finished(self):
        self.preview_voice_btn.setEnabled(True)

    def _play_preview(self, path):
        self._preview_player.setSource(QUrl.fromLocalFile(path))
        self._preview_player.play()

    def _preview_error(self, message):
        QMessageBox.warning(self, "Voice preview failed", message)


class CharacterPanelWidget(QWidget):
    """Cast list container displaying cards for all detected characters."""

    character_updated = Signal()

    def __init__(self, voice_library: Optional[VoiceLibrary] = None, parent=None):
        super().__init__(parent)
        self.voice_library = voice_library or VoiceLibrary()
        self._project: Optional[Project] = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        header = QLabel("🎭 Cast & Voice Profiles")
        header.setStyleSheet("font-size: 15px; font-weight: bold; color: #E0E7FF; padding: 6px;")
        layout.addWidget(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.cards_layout = QVBoxLayout(self.container)
        self.cards_layout.setContentsMargins(6, 6, 6, 6)
        self.cards_layout.setSpacing(12)
        self.cards_layout.addStretch(1)
        self.scroll.setWidget(self.container)

        layout.addWidget(self.scroll)

    def load_project(self, project: Project):
        self._project = project
        self.refresh()

    def refresh(self):
        if not self._project:
            return

        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for name, profile in self._project.speakers.items():
            card = SpeakerCard(name, profile, self.voice_library)
            card.voice_changed.connect(lambda: self.character_updated.emit())
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
