"""Application entry point and Qt initialization."""

import sys
from PySide6.QtWidgets import QApplication
from app.ui.theme import apply_studio_theme
from app.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Natural Voice Studio")
    app.setOrganizationName("NaturalAudio")

    apply_studio_theme(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
