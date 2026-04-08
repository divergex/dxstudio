"""
dxstudio.gui.main_window — Top-level Qt MainWindow.

Layout:
    ┌──────────────────────────────────────────────┐
    │  Menu bar                                    │
    ├───────────┬──────────────────────────────────┤
    │ Strategy  │  Results / Charts (central area) │
    │ Explorer  │                                  │
    │  (left)   ├──────────────────────────────────┤
    │           │  Command Palette (bottom)         │
    └───────────┴──────────────────────────────────┘
    │  Status bar                                  │
    └──────────────────────────────────────────────┘

The window is a thin orchestration shell: all business logic is
delegated to self._core (StudioCore). The GUI never calls dxlib directly.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDockWidget,
    QMainWindow,
    QStatusBar,
)
from PySide6.QtCore import Qt

from ..core.studio import StudioCore
from .panels.strategy_explorer import StrategyExplorerPanel
from .panels.results_viewer import ResultsViewerPanel
from .panels.workflow_editor import WorkflowEditorPanel
from .panels.command_palette import CommandPalettePanel
from .widgets.menu_bar import build_menu_bar


class MainWindow(QMainWindow):
    """
    Primary application window for dxstudio.
    """

    def __init__(self, core: StudioCore, parent=None) -> None:
        super().__init__(parent)
        self._core = core

        self.setWindowTitle("dxstudio")
        self.setMinimumSize(1200, 800)

        self._build_ui()
        self._connect_signals()

        self.status_bar.showMessage("Ready.")

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # Menu bar
        self.setMenuBar(build_menu_bar(self, self._core))

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Central splitter: results viewer occupies the main area
        self.results_viewer = ResultsViewerPanel(core=self._core, parent=self)
        self.setCentralWidget(self.results_viewer)

        # Left dock: strategy explorer
        self.strategy_explorer = StrategyExplorerPanel(core=self._core, parent=self)
        left_dock = QDockWidget("Strategies", self)
        left_dock.setWidget(self.strategy_explorer)
        left_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, left_dock)

        # Right dock: workflow editor
        self.workflow_editor = WorkflowEditorPanel(core=self._core, parent=self)
        right_dock = QDockWidget("Workflow", self)
        right_dock.setWidget(self.workflow_editor)
        right_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, right_dock)

        # Bottom dock: command palette
        self.command_palette = CommandPalettePanel(core=self._core, parent=self)
        bottom_dock = QDockWidget("Command Palette", self)
        bottom_dock.setWidget(self.command_palette)
        bottom_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, bottom_dock)

    # ------------------------------------------------------------------
    # Signal wiring
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        # When a strategy is selected in the explorer, update status bar
        self.strategy_explorer.strategy_selected.connect(self._on_strategy_selected)

        # When the command palette runs a command, refresh results
        self.command_palette.command_executed.connect(self._on_command_executed)

        # When the workflow editor requests execution
        self.workflow_editor.workflow_run_requested.connect(self._on_workflow_run)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_strategy_selected(self, path: str) -> None:
        self.status_bar.showMessage(f"Selected strategy: {path}")

    def _on_command_executed(self, output: str) -> None:
        self.status_bar.showMessage("Command executed.")
        # Refresh results panel in case a backtest ran
        self.results_viewer.refresh()

    def _on_workflow_run(self, workflow_yaml: str) -> None:
        import tempfile, os
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(workflow_yaml)
            tmp_path = f.name
        try:
            self._core.execute_workflow_file(tmp_path)
            self.results_viewer.refresh()
            self.status_bar.showMessage("Workflow executed successfully.")
        except Exception as exc:  # noqa: BLE001
            self.status_bar.showMessage(f"Workflow error: {exc}")
        finally:
            os.unlink(tmp_path)