"""Main Window of the Personal Local Natural Multi-Voice Audio Studio."""

import os
import subprocess
from pathlib import Path
from typing import Optional
from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QLabel,
    QPushButton,
    QComboBox,
    QFileDialog,
    QMessageBox,
    QFrame,
    QStatusBar,
)
from PySide6.QtGui import QAction

from app.models.project import Project
from app.projects.manager import ProjectManager
from app.voices.library import VoiceLibrary
from app.ui.script_editor import ScriptEditorWidget
from app.ui.character_panel import CharacterPanelWidget
from app.ui.audio_player import StudioAudioPlayer
from app.ui.voice_library_dialog import VoiceLibraryDialog
from app.ui.pronunciation_dialog import PronunciationDialog
from app.ui.settings_dialog import SettingsDialog
from app.ui.generation_view import GenerationProgressDialog
from app.audio.generator import AudioGenerationEngine
from app.audio.assembler import TimelineAssembler
from app.system.resources import SystemResourceManager, SystemSnapshot
from app.system.limits import set_system_profile, get_system_limits


SAMPLE_SCRIPT = """# Episode 1 — Local AI and Voice Synthesis

Host: Welcome back to the show. Today we're talking about local AI voice synthesis, and running high quality audio tools at zero cost.

Co-Host: I've been looking forward to this one! There's an incredible amount of momentum in this space right now.

Host: There really is. Let's start with the basics for our listeners.

Guest: Thanks for having me. I think the easiest way to understand local voice models is that your computer processes everything offline without sending voice data to cloud servers.

Host [curious]: That distinction is crucial. Can you break that down?

Guest: Absolutely. Everything from dynamic character detection to neural speech generation happens right on your machine, respecting your hardware and keeping your scripts completely private.

Co-Host [excited]: Exactly! And with smart caching, you never have to re-generate lines that haven't changed.

Host: That's a great workflow. Let's dive deeper into how speech direction and prosody work.
"""


class MainWindow(QMainWindow):
    """Studio Main Application Window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Personal Multi-Voice Natural Audio Studio ($0 Local Studio)")
        self.resize(1300, 860)

        self.voice_library = VoiceLibrary()
        self.project_manager = ProjectManager(voice_library=self.voice_library)
        self.current_project: Optional[Project] = None

        self._init_ui()
        self._load_initial_project()
        self._init_system_monitor()

    def _init_ui(self):
        # Menu Bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")

        new_act = QAction("New Project", self)
        new_act.setShortcut("Ctrl+N")
        new_act.triggered.connect(self._on_new_project)
        file_menu.addAction(new_act)

        open_act = QAction("Open Project...", self)
        open_act.setShortcut("Ctrl+O")
        open_act.triggered.connect(self._on_open_project)
        file_menu.addAction(open_act)
        import_act = QAction("Open Script (.md / .txt)...", self)
        import_act.triggered.connect(self._on_import_script)
        file_menu.addAction(import_act)

        save_act = QAction("Save Project", self)
        save_act.setShortcut("Ctrl+S")
        save_act.triggered.connect(self._on_save_project)
        file_menu.addAction(save_act)

        file_menu.addSeparator()

        sample_act = QAction("Load Sample Script", self)
        sample_act.triggered.connect(self._load_sample_script)
        file_menu.addAction(sample_act)

        tools_menu = menubar.addMenu("Studio Tools")
        voices_act = QAction("Voice Library & Cloning...", self)
        voices_act.triggered.connect(self._open_voice_library)
        tools_menu.addAction(voices_act)

        pronounce_act = QAction("Pronunciation Dictionary...", self)
        pronounce_act.triggered.connect(self._open_pronunciation)
        tools_menu.addAction(pronounce_act)

        settings_act = QAction("Speech Engine Setup...", self)
        settings_act.triggered.connect(self._open_settings)
        tools_menu.addAction(settings_act)

        # Central Widget & Layout
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(12, 8, 12, 8)
        root_layout.setSpacing(10)

        # Studio Control Header Bar
        header = QFrame()
        header.setStyleSheet("background-color: #18181B; border: 1px solid #27272A; border-radius: 8px;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(14, 10, 14, 10)
        h_layout.setSpacing(12)

        self.project_title_lbl = QLabel("🎙 Untitled Episode")
        self.project_title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        h_layout.addWidget(self.project_title_lbl)

        h_layout.addStretch(1)

        # Performance Profile
        h_layout.addWidget(QLabel("Profile:"))
        self.profile_combo = QComboBox()
        self.profile_combo.addItem("Balanced (Default)", "balanced")
        self.profile_combo.addItem("Safe (Low Resource)", "safe")
        self.profile_combo.addItem("Performance (Fast)", "performance")
        self.profile_combo.currentIndexChanged.connect(self._on_profile_changed)
        h_layout.addWidget(self.profile_combo)

        # Studio Quality Mode Selector
        h_layout.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Studio Direction", "studio")
        self.mode_combo.addItem("Standard Direction", "standard")
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        h_layout.addWidget(self.mode_combo)

        # Export Format
        h_layout.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["MP3", "WAV", "M4A", "FLAC"])
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        h_layout.addWidget(self.format_combo)

        # Primary Generate Button
        self.generate_btn = QPushButton("🎙 Generate Master Audio")
        self.generate_btn.setObjectName("PrimaryButton")
        self.generate_btn.setFixedHeight(34)
        self.generate_btn.clicked.connect(self._on_generate_audio)
        h_layout.addWidget(self.generate_btn)

        # Tools shortcuts
        self.voice_lib_btn = QPushButton("📚 Voices")
        self.voice_lib_btn.clicked.connect(self._open_voice_library)
        h_layout.addWidget(self.voice_lib_btn)

        self.open_folder_btn = QPushButton("📁 Folder")
        self.open_folder_btn.clicked.connect(self._on_open_folder)
        h_layout.addWidget(self.open_folder_btn)

        root_layout.addWidget(header)
        from PySide6.QtWidgets import QCheckBox
        self.online_checkbox = QCheckBox("Allow Edge voices to send my script text to Microsoft (optional online speech)")
        self.online_checkbox.toggled.connect(self._on_online_changed)
        root_layout.addWidget(self.online_checkbox)
        guidance = QLabel("Paste or open your script → choose voices → preview → generate. "
                          "Only your dialogue is spoken. Kokoro needs one-time model setup under Studio Tools.")
        guidance.setWordWrap(True)
        root_layout.addWidget(guidance)

        # Main Splitter (Left: Script & Turn Cards, Right: Cast Panel)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        self.script_editor = ScriptEditorWidget()
        self.script_editor.markdown_modified.connect(self._on_markdown_modified)
        self.script_editor.take_selection_modified.connect(self._on_character_updated)
        self.script_editor.single_turn_generate_requested.connect(self._on_single_turn_generate)
        self.splitter.addWidget(self.script_editor)

        self.character_panel = CharacterPanelWidget(self.voice_library)
        self.character_panel.character_updated.connect(self._on_character_updated)
        self.splitter.addWidget(self.character_panel)

        self.splitter.setSizes([750, 450])
        root_layout.addWidget(self.splitter, 1)

        # Master Audio Player at Bottom
        self.player_widget = StudioAudioPlayer()
        root_layout.addWidget(self.player_widget)

        # Status Bar with Resource Monitor
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.res_label = QLabel("Initializing System Monitor...")
        self.res_label.setStyleSheet("color: #A1A1AA; font-family: monospace; font-size: 11px;")
        self.status_bar.addPermanentWidget(self.res_label)

    def _init_system_monitor(self):
        self._sys_timer = QTimer(self)
        self._sys_timer.timeout.connect(self._update_system_stats)
        self._sys_timer.start(3000)  # Update every 3 seconds
        self._update_system_stats()

    def _update_system_stats(self):
        snap: SystemSnapshot = SystemResourceManager.get_snapshot()
        vram_str = f"VRAM: {snap.vram_used_mb}MB" if snap.vram_total_mb > 0 else "GPU: CPU Mode"
        self.res_label.setText(
            f"CPU: {snap.cpu_percent}% | "
            f"RAM: {snap.ram_used_gb}/{snap.ram_total_gb}GB | "
            f"{vram_str} | "
            f"Disk Free: {snap.free_disk_gb}GB"
        )

    def _on_profile_changed(self):
        prof = self.profile_combo.currentData()
        set_system_profile(prof)

    def _load_initial_project(self):
        proj = self.project_manager.create_project("Your Script", "")
        self._set_project(proj)

    def _set_project(self, project: Project):
        self.current_project = project
        self.online_checkbox.setChecked(project.settings.allow_online)
        self.format_combo.setCurrentText(project.settings.output_format.upper())
        self.mode_combo.setCurrentIndex(max(0, self.mode_combo.findData(project.settings.generation_mode)))
        self.project_title_lbl.setText(f"🎙 {project.name}")
        self.script_editor.load_project(project)
        self.script_editor.tabs.setCurrentIndex(0 if project.script_nodes else 1)
        self.character_panel.load_project(project)
        self._update_master_player()

    def _update_master_player(self):
        if self.current_project and self.current_project.final_audio_path:
            p_path = self.current_project.final_audio_path
            if Path(p_path).exists():
                markers = []
                if self.current_project.manifest:
                    for item in self.current_project.manifest.items:
                        if item.item_type == "audio":
                            markers.append((item.start_time_ms, item.speaker or "Speaker"))
                self.player_widget.load_audio(p_path, self.current_project.name, markers)

    def _on_markdown_modified(self, new_text: str):
        if not self.current_project:
            return
        self.project_manager.sync_markdown_to_project(self.current_project, new_text)
        self.character_panel.refresh()
        self.script_editor.refresh_cards()
        self.project_manager.save_project(self.current_project)

    def _on_character_updated(self):
        if self.current_project:
            self.project_manager.save_project(self.current_project)

    def _on_mode_changed(self):
        if self.current_project:
            self.current_project.settings.generation_mode = self.mode_combo.currentData()

    def _on_format_changed(self, text: str):
        if self.current_project:
            self.current_project.settings.output_format = text.lower()

    def _on_generate_audio(self):
        if not self.current_project:
            return

        self.project_manager.save_project(self.current_project)
        p_dir = self.project_manager.get_project_dir(self.current_project.id)

        dlg = GenerationProgressDialog(self.current_project, p_dir, self)
        dlg.generation_finished.connect(self._on_generation_finished)
        dlg.exec()

    def _on_generation_finished(self, success: bool):
        if self.current_project:
            self.project_manager.save_project(self.current_project)
        if success and self.current_project:
            self.script_editor.refresh_cards()
            self._update_master_player()
            self.player_widget.play()

    def _on_single_turn_generate(self, segment_id: str, force_new_take: bool):
        if not self.current_project:
            return
        from app.ui.task_worker import TaskWorker
        project = self.current_project
        p_dir = self.project_manager.get_project_dir(project.id)
        def task():
            engine = AudioGenerationEngine()
            if not engine.generate_single_turn(project, p_dir, segment_id, force_new_take):
                info = project.segments_generation.get(segment_id)
                raise RuntimeError(info.error_message if info else "Turn not found")
            # A preview should succeed even when the rest of the episode is not generated.
            return project.segments_generation[segment_id].active_take.audio_path
        self.centralWidget().setEnabled(False)
        self._turn_worker = TaskWorker(task, self)
        self._turn_worker.result_ready.connect(self._on_turn_ready)
        self._turn_worker.failed.connect(lambda msg: QMessageBox.warning(self, "Turn failed", msg))
        self._turn_worker.finished.connect(lambda: self.centralWidget().setEnabled(True))
        self._turn_worker.start()

    def _on_turn_ready(self, path):
        self.project_manager.save_project(self.current_project)
        self.script_editor.refresh_cards()
        self.player_widget.load_audio(path, "Turn preview", [])
        self.player_widget.play()

    def _on_online_changed(self, enabled):
        if self.current_project:
            self.current_project.settings.allow_online = enabled
            self.project_manager.save_project(self.current_project)

    def _on_import_script(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open script", "", "Scripts (*.md *.txt)")
        if path:
            try:
                text = Path(path).read_text(encoding="utf-8-sig")
                self._set_project(self.project_manager.create_project(Path(path).stem, text))
            except Exception as exc:
                QMessageBox.warning(self, "Cannot open script", str(exc))

    def closeEvent(self, event):
        from app.ui.task_worker import TaskWorker
        if any(worker.isRunning() for worker in self.findChildren(TaskWorker)):
            QMessageBox.information(self, "Speech is running", "Wait for the current voice preview or turn to finish.")
            event.ignore()
            return
        if self.current_project:
            self.project_manager.save_project(self.current_project)
        event.accept()

    def _on_new_project(self):
        proj = self.project_manager.create_project("Untitled Episode", "")
        self._set_project(proj)

    def _on_open_project(self):
        projects = self.project_manager.list_projects()
        if not projects:
            QMessageBox.information(self, "No Projects", "No existing projects found.")
            return

        proj_id = QFileDialog.getExistingDirectory(
            self,
            "Open Project Directory",
            str(self.project_manager.root_dir),
        )
        if proj_id:
            dir_path = Path(proj_id)
            p = self.project_manager.load_project(dir_path.name)
            if p:
                self._set_project(p)

    def _on_save_project(self):
        if self.current_project:
            self.project_manager.save_project(self.current_project)
            QMessageBox.information(self, "Project Saved", f"Project '{self.current_project.name}' saved.")

    def _load_sample_script(self):
        if self.current_project:
            self.current_project.markdown = SAMPLE_SCRIPT
            self._on_markdown_modified(SAMPLE_SCRIPT)
            self.script_editor.load_project(self.current_project)

    def _open_voice_library(self):
        dlg = VoiceLibraryDialog(self.voice_library, self)
        dlg.library_updated.connect(lambda: self.character_panel.refresh())
        dlg.exec()

    def _open_pronunciation(self):
        dlg = PronunciationDialog(self.current_project, self)
        dlg.exec()

    def _open_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec()

    def _on_open_folder(self):
        if self.current_project:
            p_dir = self.project_manager.get_project_dir(self.current_project.id)
            if os.name == 'nt':
                os.startfile(str(p_dir))
            else:
                subprocess.Popen(["xdg-open", str(p_dir)])
