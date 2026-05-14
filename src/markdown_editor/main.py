"""Entry point for the Markdown Editor application."""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from markdown_editor.app import AppWindow


def main() -> int:
    """Launch the Markdown Editor application.

    Optionally accepts a file path as the first command-line argument.
    """
    app = QApplication(sys.argv)
    app.setApplicationName("Markdown Editor")
    app.setOrganizationName("markdown-editor")
    app.setOrganizationDomain("markdown-editor.local")

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
