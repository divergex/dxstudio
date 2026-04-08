"""
dxstudio.gui.app — Qt application bootstrap.

Imported lazily to avoid forcing PySide6 as a hard dependency.
Only imported when dxstudio[gui] is installed.

Usage:
    from dxstudio.gui.app import run_gui
    run_gui()
"""

from __future__ import annotations

import sys


def run_gui(core=None) -> int:
    """
    Launch the dxstudio Qt GUI.

    Args:
        core: Optional pre-configured StudioCore instance.
               If None, a fresh StudioCore is created.

    Returns:
        Application exit code.
    """
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print(
            "PySide6 is not installed. Install the GUI extras:\n"
            "    pip install dxstudio[gui]",
            file=sys.stderr,
        )
        return 1

    from ..core.studio import StudioCore
    from .main_window import MainWindow

    if core is None:
        core = StudioCore()

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("dxstudio")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("dxstudio")

    window = MainWindow(core=core)
    window.show()

    return app.exec()