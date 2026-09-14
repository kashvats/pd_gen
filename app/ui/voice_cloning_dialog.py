"""Voice Cloning Wizard with quality diagnostics, reference audio preservation, and consent gate."""

from pathlib import Path
from typing import List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QCheckBox,
    QFileDialog,
    QListWidget,
    QProgressBar,
    QTextEdit,
    QMessageBox,
    QGroupBox,
)

from app.voices.quality import analyze_reference_audio, AudioQualityReport
from app.voices.cloning import VoiceCloningService
from app.voices.library import VoiceLibrary
from app.tts.registry import tts_registry


class VoiceCloningDialog(QDialog):
    """Voice Cloning Wizard dialog."""

    voice_cloned = Signal()

    def __init__(self, voice_library: Optional[VoiceLibrary] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Voice Clone — AI Voice Studio")
        self.setMinimumSize(580, 680)
        self.voice_library = voice_library or VoiceLibrary()
        self.cloning_service = VoiceCloningService(self.voice_library)
        self.selected_files: List[str] = []

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("🎙 Create New Voice Clone")
        title.setStyleSheet("font-size: 17px; font-weight: bold; color: #FFFFFF;")
        layout.addWidget(title)

        subtitle = QLabel("Upload clean reference recordings to clone a voice with high fidelity.")
        subtitle.setStyleSheet("color: #94A3B8; font-size: 12px;")
        layout.addWidget(subtitle)

        # Basic Info Group
        info_group = QGroupBox("1. Voice Profile Details")
        info_layout = QVBoxLayout(info_group)

        row1 = QHBoxLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. My Host Voice, Sarah, Dr. Lee")
        row1.addWidget(QLabel("Voice Name:"))
        row1.addWidget(self.name_edit, 1)

        self.provider_combo = QComboBox()
        for p in tts_registry.list_providers():
            if p.capabilities.voice_cloning:
                self.provider_combo.addItem(p.display_name, p.provider_id)
        row1.addWidget(QLabel("Provider:"))
        row1.addWidget(self.provider_combo)
        info_layout.addLayout(row1)

        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("Optional description or speaking characteristics")
        info_layout.addWidget(QLabel("Description:"))
        info_layout.addWidget(self.desc_edit)

        layout.addWidget(info_group)

        # Reference Audio Group
        ref_group = QGroupBox("2. Reference Audio Samples")
        ref_layout = QVBoxLayout(ref_group)

        btn_row = QHBoxLayout()
        self.add_files_btn = QPushButton("📁 Select Audio Files...")
        self.add_files_btn.clicked.connect(self._select_files)
        self.clear_files_btn = QPushButton("Clear")
        self.clear_files_btn.clicked.connect(self._clear_files)

        btn_row.addWidget(self.add_files_btn)
        btn_row.addWidget(self.clear_files_btn)
        btn_row.addStretch(1)
        ref_layout.addLayout(btn_row)

        self.file_list = QListWidget()
        self.file_list.setFixedHeight(75)
        ref_layout.addWidget(self.file_list)

        # Quality Diagnostic Panel
        self.quality_group = QGroupBox("Sample Quality Diagnostics")
        q_layout = QVBoxLayout(self.quality_group)

        self.quality_bar = QProgressBar()
        self.quality_bar.setRange(0, 100)
        self.quality_bar.setValue(0)
        self.quality_bar.setFormat("Sample Quality: Not Tested")
        q_layout.addWidget(self.quality_bar)

        self.quality_details = QLabel("Select 1-3 minutes of clean audio without background music or echo.")
        self.quality_details.setStyleSheet("color: #A1A1AA; font-size: 11px;")
        self.quality_details.setWordWrap(True)
        q_layout.addWidget(self.quality_details)

        ref_layout.addWidget(self.quality_group)
        layout.addWidget(ref_group)

        # Permission & Consent Group
        consent_group = QGroupBox("3. Permission Confirmation")
        c_layout = QVBoxLayout(consent_group)

        self.consent_checkbox = QCheckBox(
            "I confirm that this is my voice or that I have permission\n"
            "from the speaker to create and use this voice clone."
        )
        self.consent_checkbox.setStyleSheet("font-weight: 600; color: #F1F5F9;")
        c_layout.addWidget(self.consent_checkbox)

        self.consent_notes_edit = QLineEdit()
        self.consent_notes_edit.setPlaceholderText("Optional notes / consent verification details")
        c_layout.addWidget(self.consent_notes_edit)

        layout.addWidget(consent_group)

        # Footer Actions
        footer = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)

        self.clone_btn = QPushButton("✨ Create Cloned Voice")
        self.clone_btn.setObjectName("PrimaryButton")
        self.clone_btn.setFixedHeight(34)
        self.clone_btn.clicked.connect(self._start_cloning)

        footer.addStretch(1)
        footer.addWidget(self.cancel_btn)
        footer.addWidget(self.clone_btn)
        layout.addLayout(footer)

    def _select_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Voice Reference Audio",
            "",
            "Audio Files (*.wav *.mp3 *.m4a *.flac *.ogg);;All Files (*)",
        )
        if files:
            self.selected_files.extend(files)
            self._update_file_list()

    def _clear_files(self):
        self.selected_files.clear()
        self._update_file_list()

    def _update_file_list(self):
        self.file_list.clear()
        for f in self.selected_files:
            self.file_list.addItem(Path(f).name)

        if self.selected_files:
            # Analyze primary sample
            report: AudioQualityReport = analyze_reference_audio(self.selected_files[0])
            self.quality_bar.setValue(report.score)
            self.quality_bar.setFormat(f"Sample Quality: {report.status} ({report.score}/100)")

            notes = [f"Duration: {report.duration_sec:.1f}s | RMS: {report.rms_db} dB | Peak: {report.peak_db} dB"]
            if report.warnings:
                notes.extend(report.warnings)
            if report.guidance:
                notes.extend(report.guidance)
            self.quality_details.setText("\n• ".join(["• " + notes[0]] + notes[1:]))
        else:
            self.quality_bar.setValue(0)
            self.quality_bar.setFormat("Sample Quality: No File Selected")
            self.quality_details.setText("Select 1-3 minutes of clean speech without music or echo.")

    def _start_cloning(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing Name", "Please specify a name for the voice clone.")
            return

        if not self.selected_files:
            QMessageBox.warning(self, "Missing Audio", "Please select at least one reference audio sample.")
            return

        if not self.consent_checkbox.isChecked():
            QMessageBox.warning(
                self,
                "Permission Required",
                "You must confirm ownership or speaker permission before cloning a voice.",
            )
            return

        provider_id = self.provider_combo.currentData()
        self.clone_btn.setEnabled(False)
        self.clone_btn.setText("Cloning Voice...")

        success, profile, err = self.cloning_service.clone_voice(
            name=name,
            provider_id=provider_id,
            reference_file_paths=self.selected_files,
            consent_confirmed=True,
            consent_notes=self.consent_notes_edit.text(),
            description=self.desc_edit.text(),
        )

        self.clone_btn.setEnabled(True)
        self.clone_btn.setText("✨ Create Cloned Voice")

        if success and profile:
            QMessageBox.information(
                self,
                "Voice Cloned",
                f"Successfully cloned voice '{profile.name}'!\nIt is now saved in your local Voice Library.",
            )
            self.voice_cloned.emit()
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "Cloning Failed",
                f"Could not clone voice:\n{err}",
            )
