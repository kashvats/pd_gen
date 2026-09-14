"""Asynchronous generation worker and progress dialog with pause, resume, cancel, and planning."""

from pathlib import Path
from typing import Optional
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QListWidget,
    QGroupBox,
)

from app.models.project import Project
from app.audio.generator import AudioGenerationEngine, GenerationPlan
from app.audio.assembler import TimelineAssembler


class GenerationWorker(QThread):
    """Background worker thread for speech synthesis and timeline assembly."""

    progress_updated = Signal(str, float)
    finished_success = Signal()
    finished_error = Signal(str)

    def __init__(self, project: Project, project_dir: Path, parent=None):
        super().__init__(parent)
        self.project = project
        self.project_dir = project_dir
        self._is_cancelled = False
        self._is_paused = False
        self.engine = AudioGenerationEngine()

    def cancel(self):
        self._is_cancelled = True

    def toggle_pause(self) -> bool:
        self._is_paused = not self._is_paused
        return self._is_paused

    def is_paused(self) -> bool:
        return self._is_paused

    def run(self):
        try:
            self.progress_updated.emit("Analyzing conversational context & checking cache...", 0.05)

            # Step 1: Synthesize missing speech segments with pause and cancel checks
            success = self.engine.generate_project(
                project=self.project,
                project_dir=self.project_dir,
                progress_callback=lambda msg, pct: self.progress_updated.emit(msg, pct),
                cancel_check=lambda: self._is_cancelled,
                pause_check=lambda: self._is_paused,
            )

            if self._is_cancelled:
                self.finished_error.emit("Generation was cancelled safely.")
                return

            if not success:
                errors = [g.error_message for g in self.project.segments_generation.values() if g.status == "failed"]
                self.finished_error.emit("; ".join(errors) or "No dialogue to generate. Use Speaker: text.")
                return

            # Step 2: Assemble timeline and apply gentle mastering
            self.progress_updated.emit("Assembling timeline & applying gentle studio mastering...", 0.90)
            manifest = TimelineAssembler.assemble(self.project, self.project_dir)

            if not manifest:
                self.finished_error.emit("Timeline assembly failed.")
                return

            self.progress_updated.emit("Master audio generated successfully!", 1.0)
            self.finished_success.emit()

        except Exception as err:
            self.finished_error.emit(str(err))


class GenerationProgressDialog(QDialog):
    """Progress dialog tracking generation state with planning and pause/resume/cancel."""

    generation_finished = Signal(bool)

    def __init__(self, project: Project, project_dir: Path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generating Audio — AI Voice Studio")
        self.setMinimumSize(520, 320)
        self.setModal(True)

        self.project = project
        self.project_dir = project_dir
        self.engine = AudioGenerationEngine()

        self._init_ui()
        self._show_plan()
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self._start_generation)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        self.title_lbl = QLabel("🎙 Studio Audio Generation")
        self.title_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #FFFFFF;")
        layout.addWidget(self.title_lbl)

        # Plan Summary Box
        self.plan_box = QGroupBox("Generation Plan")
        p_layout = QHBoxLayout(self.plan_box)
        self.plan_label = QLabel("Analyzing script...")
        self.plan_label.setStyleSheet("color: #C7D2FE; font-size: 12px;")
        p_layout.addWidget(self.plan_label)
        layout.addWidget(self.plan_box)

        self.status_lbl = QLabel("Initializing pipeline...")
        self.status_lbl.setStyleSheet("color: #94A3B8; font-size: 12px;")
        layout.addWidget(self.status_lbl)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.log_list = QListWidget()
        self.log_list.setFixedHeight(90)
        layout.addWidget(self.log_list)

        btn_row = QHBoxLayout()
        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.clicked.connect(self._on_pause_toggle)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._on_cancel)

        btn_row.addWidget(self.pause_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(self.cancel_btn)
        layout.addLayout(btn_row)

    def _show_plan(self):
        plan: GenerationPlan = self.engine.plan_generation(self.project)
        self.plan_label.setText(
            f"Total Turns: {plan.total_turns}  |  "
            f"Cached: {plan.cached_turns}  |  "
            f"Locked: {plan.locked_turns}  |  "
            f"Need Synthesis: {plan.need_synthesis_turns}"
        )

    def _start_generation(self):
        self._completed_success = False
        self.worker = GenerationWorker(self.project, self.project_dir, self)
        self.worker.finished.connect(self._thread_finished)
        self.worker.progress_updated.connect(self._on_progress)
        self.worker.finished_success.connect(self._on_success)
        self.worker.finished_error.connect(self._on_error)
        self.worker.start()

    def _on_progress(self, msg: str, pct: float):
        self.status_lbl.setText(msg)
        self.progress_bar.setValue(int(pct * 100))
        self.log_list.addItem(msg)
        self.log_list.scrollToBottom()

    def _on_pause_toggle(self):
        if hasattr(self, 'worker') and self.worker.isRunning():
            is_paused = self.worker.toggle_pause()
            if is_paused:
                self.pause_btn.setText("▶ Resume")
                self.status_lbl.setText("Generation paused. Click Resume to continue.")
            else:
                self.pause_btn.setText("⏸ Pause")
                self.status_lbl.setText("Resuming generation...")

    def _on_success(self):
        self.status_lbl.setText("✨ Final master audio generated successfully!")
        self.progress_bar.setValue(100)
        self.pause_btn.setEnabled(False)
        self.cancel_btn.setText("Close")
        self.generation_finished.emit(True)
        self._completed_success = True

    def _thread_finished(self):
        if self._completed_success:
            self.accept()

    def _on_error(self, err_msg: str):
        self.status_lbl.setText(f"❌ {err_msg}")
        self.status_lbl.setStyleSheet("color: #EF4444; font-weight: bold;")
        self.pause_btn.setEnabled(False)
        self.cancel_btn.setText("Close")
        self.generation_finished.emit(False)

    def _on_cancel(self):
        self.reject()

    def reject(self):
        if hasattr(self, "worker") and self.worker.isRunning():
            self.worker.cancel()
            self.status_lbl.setText("Cancelling after the current operation. Completed takes will be kept.")
            self.cancel_btn.setEnabled(False)
            self.worker.finished.connect(self._close_after_cancel)
            return
        super().reject()

    def _close_after_cancel(self):
        self.generation_finished.emit(False)
        super().reject()

    def closeEvent(self, event):
        if hasattr(self, "worker") and self.worker.isRunning():
            event.ignore()
            self.reject()
        else:
            event.accept()
