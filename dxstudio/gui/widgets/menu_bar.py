"""
dxstudio.gui.widgets.menu_bar — Application menu bar factory.
"""

from __future__ import annotations

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFileDialog, QMenuBar, QMessageBox

from dxstudio.core import StudioCore


def build_menu_bar(parent, core: StudioCore) -> QMenuBar:
    bar = QMenuBar(parent)

    # ------------------------------------------------------------------ File
    file_menu = bar.addMenu("File")

    act_open = QAction("Open Strategy…", parent)
    act_open.setShortcut("Ctrl+O")
    act_open.triggered.connect(lambda: _open_strategy(parent, core))
    file_menu.addAction(act_open)

    act_run_wf = QAction("Run Workflow…", parent)
    act_run_wf.setShortcut("Ctrl+R")
    act_run_wf.triggered.connect(lambda: _run_workflow(parent, core))
    file_menu.addAction(act_run_wf)

    file_menu.addSeparator()

    act_quit = QAction("Quit", parent)
    act_quit.setShortcut("Ctrl+Q")
    act_quit.triggered.connect(parent.close)
    file_menu.addAction(act_quit)

    # --------------------------------------------------------------- Session
    session_menu = bar.addMenu("Session")

    act_new_session = QAction("New Session", parent)
    act_new_session.triggered.connect(lambda: core.new_session())
    session_menu.addAction(act_new_session)

    # ----------------------------------------------------------------- Help
    help_menu = bar.addMenu("Help")

    act_about = QAction("About dxstudio", parent)
    act_about.triggered.connect(lambda: QMessageBox.about(
        parent,
        "About dxstudio",
        "<b>dxstudio</b> v0.1.0<br>"
        "Multi-interface execution platform for quantitative strategies.<br><br>"
        "Built on top of dxlib.",
    ))
    help_menu.addAction(act_about)

    return bar


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _open_strategy(parent, core: StudioCore) -> None:
    path, _ = QFileDialog.getOpenFileName(
        parent,
        "Open Strategy",
        "",
        "Strategy Files (*.dxs);;All Files (*)",
    )
    if path:
        try:
            core.load_strategy(path)
            parent.status_bar.showMessage(f"Loaded: {path}")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(parent, "Load Error", str(exc))


def _run_workflow(parent, core: StudioCore) -> None:
    path, _ = QFileDialog.getOpenFileName(
        parent,
        "Open Workflow",
        "",
        "Workflow Files (*.yaml *.yml);;All Files (*)",
    )
    if path:
        try:
            core.execute_workflow_file(path)
            parent.results_viewer.refresh()
            parent.status_bar.showMessage("Workflow complete.")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(parent, "Workflow Error", str(exc))