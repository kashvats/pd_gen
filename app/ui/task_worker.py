"""Small bounded worker for previews and individual turns."""
from PySide6.QtCore import QThread, Signal


class TaskWorker(QThread):
    result_ready = Signal(object)
    failed = Signal(str)

    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task

    def run(self):
        try:
            self.result_ready.emit(self.task())
        except Exception as exc:
            self.failed.emit(str(exc))
