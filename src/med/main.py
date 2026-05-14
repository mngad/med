"""Entry point for med."""

import os
import sys
from pathlib import Path

# Suppress Qt font-population timing warnings on macOS.
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.fonts=false")

from PySide6.QtWidgets import QApplication

from med.app import AppWindow


def main() -> int:
    """Launch med.

    Optionally accepts a file path as the first command-line argument.
    """
    app = QApplication(sys.argv)
    app.setApplicationName("med")
    app.setOrganizationName("med")
    app.setOrganizationDomain("med.local")

    # Open a file passed on the command line, if any.
    file_path = None
    if len(sys.argv) > 1:
        candidate = Path(sys.argv[1]).resolve()
        if candidate.is_file():
            file_path = str(candidate)

    window = AppWindow(file_path=file_path)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
