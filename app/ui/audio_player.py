"""Integrated Studio Audio Player with waveform scrubber, timeline jump, and speed controls."""

from pathlib import Path
from typing import Optional, List, Tuple
from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QSlider,
    QLabel,
    QComboBox,
    QFrame,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput


class StudioAudioPlayer(QWidget):
    """Audio player widget with timeline navigation and speed controls."""

    seek_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_file: Optional[str] = None
        self._duration_ms = 0
        self._markers: List[Tuple[int, str]] = []  # List of (timestamp_ms, label)

        self._player = QMediaPlayer(self)
        self._audio_output = QAudioOutput(self)
        self._player.setAudioOutput(self._audio_output)
        self._audio_output.setVolume(0.9)

        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)
        self._player.playbackStateChanged.connect(self._on_state_changed)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)

        # Timeline Scrubber Row
        scrub_row = QHBoxLayout()
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("color: #A1A1AA; font-family: monospace; font-size: 12px;")

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 1000)
        self.slider.sliderMoved.connect(self._on_slider_moved)

        scrub_row.addWidget(self.time_label)
        scrub_row.addWidget(self.slider)
        layout.addLayout(scrub_row)

        # Controls Row
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(8)

        self.prev_btn = QPushButton("⏮ Prev Turn")
        self.prev_btn.setToolTip("Jump to previous speaker turn")
        self.prev_btn.clicked.connect(self.prev_turn)

        self.play_btn = QPushButton("▶ Play Master")
        self.play_btn.setObjectName("PrimaryButton")
        self.play_btn.setMinimumWidth(110)
        self.play_btn.clicked.connect(self.toggle_play)

        self.next_btn = QPushButton("Next Turn ⏭")
        self.next_btn.setToolTip("Jump to next speaker turn")
        self.next_btn.clicked.connect(self.next_turn)

        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.75x", "1.0x", "1.25x", "1.5x", "2.0x"])
        self.speed_combo.setCurrentText("1.0x")
        self.speed_combo.currentTextChanged.connect(self._on_speed_changed)
        self.speed_combo.setFixedWidth(80)

        self.vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(90)
        self.vol_slider.setFixedWidth(80)
        self.vol_slider.setToolTip("Volume")
        self.vol_slider.valueChanged.connect(lambda v: self._audio_output.setVolume(v / 100.0))

        self.track_info_label = QLabel("No master audio loaded")
        self.track_info_label.setStyleSheet("color: #71717A; font-style: italic;")

        ctrl_row.addWidget(self.prev_btn)
        ctrl_row.addWidget(self.play_btn)
        ctrl_row.addWidget(self.next_btn)
        ctrl_row.addSpacing(12)
        ctrl_row.addWidget(QLabel("Speed:"))
        ctrl_row.addWidget(self.speed_combo)
        ctrl_row.addSpacing(8)
        ctrl_row.addWidget(QLabel("Vol:"))
        ctrl_row.addWidget(self.vol_slider)
        ctrl_row.addSpacing(12)
        ctrl_row.addWidget(self.track_info_label, 1)

        layout.addLayout(ctrl_row)

    def load_audio(self, file_path: str, title: str = "Master Track", markers: Optional[List[Tuple[int, str]]] = None):
        """Loads an audio file into the player."""
        if not file_path or not Path(file_path).exists():
            return

        self._current_file = file_path
        self._markers = sorted(markers or [], key=lambda x: x[0])
        self._player.setSource(QUrl.fromLocalFile(file_path))
        self.track_info_label.setText(f"Loaded: {title} ({Path(file_path).name})")
        self.play_btn.setEnabled(True)

    def play(self):
        if self._current_file:
            self._player.play()

    def pause(self):
        self._player.pause()

    def stop(self):
        self._player.stop()

    def toggle_play(self):
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.pause()
        else:
            self.play()

    def seek_ms(self, pos_ms: int):
        self._player.setPosition(pos_ms)

    def prev_turn(self):
        current_pos = self._player.position()
        target = 0
        for pos, _ in reversed(self._markers):
            if pos < current_pos - 1500:  # Threshold
                target = pos
                break
        self.seek_ms(target)

    def next_turn(self):
        current_pos = self._player.position()
        for pos, _ in self._markers:
            if pos > current_pos + 500:
                self.seek_ms(pos)
                break

    def _on_speed_changed(self, text: str):
        try:
            rate = float(text.replace("x", ""))
            self._player.setPlaybackRate(rate)
        except Exception:
            pass

    def _on_slider_moved(self, val: int):
        if self._duration_ms > 0:
            target_ms = int((val / 1000.0) * self._duration_ms)
            self._player.setPosition(target_ms)

    def _on_position_changed(self, pos_ms: int):
        if self._duration_ms > 0:
            pct = int((pos_ms / self._duration_ms) * 1000)
            self.slider.blockSignals(True)
            self.slider.setValue(pct)
            self.slider.blockSignals(False)
            self._update_time_label(pos_ms, self._duration_ms)

    def _on_duration_changed(self, dur_ms: int):
        self._duration_ms = dur_ms
        self._update_time_label(self._player.position(), dur_ms)

    def _on_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_btn.setText("⏸ Pause")
            self.play_btn.setObjectName("AccentButton")
        else:
            self.play_btn.setText("▶ Play Master")
            self.play_btn.setObjectName("PrimaryButton")
        self.play_btn.setStyle(self.play_btn.style())

    def _update_time_label(self, pos_ms: int, dur_ms: int):
        cur_sec = int(pos_ms / 1000)
        dur_sec = int(dur_ms / 1000)
        cur_str = f"{cur_sec // 60:02d}:{cur_sec % 60:02d}"
        dur_str = f"{dur_sec // 60:02d}:{dur_sec % 60:02d}"
        self.time_label.setText(f"{cur_str} / {dur_str}")
