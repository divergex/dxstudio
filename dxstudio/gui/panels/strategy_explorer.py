"""
dxstudio.gui.panels.strategy_explorer — Left-dock panel for browsing .dxs files.

Emits:
    strategy_selected(path: str)  — user double-clicks a strategy
    strategy_load_requested(path: str) — user clicks "Load"
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QDir, Qt, Signal
from PySide6.QtWidgets import (
    QFileSystemModel,
    QHBoxLayout,
    QPushButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from dxstudio.core import StudioCore


class StrategyExplorerPanel(QWidget):
    strategy_selected = Signal(str)
    strategy_load_requested = Signal(str)

    def __init__(self, core: StudioCore, parent=None) -> None:
        super().__init__(parent)
        self._core = core
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # File system tree filtered to .dxs files
        self._model = QFileSystemModel()
        self._model.setRootPath(QDir.homePath())
        self._model.setNameFilters(["*.dxs", "*.yaml"])
        self._model.setNameFilterDisables(False)

        self._tree = QTreeView()
        self._tree.setModel(self._model)
        self._tree.setRootIndex(self._model.index(QDir.homePath()))
        self._tree.setColumnHidden(1, True)
        self._tree.setColumnHidden(2, True)
        self._tree.setColumnHidden(3, True)
        self._tree.doubleClicked.connect(self._on_double_click)

        layout.addWidget(self._tree)

        # Buttons
        btn_row = QHBoxLayout()
        self._btn_load = QPushButton("Load")
        self._btn_load.clicked.connect(self._on_load_clicked)
        btn_row.addWidget(self._btn_load)
        layout.addLayout(btn_row)

    def _selected_path(self) -> str | None:
        index = self._tree.currentIndex()
        if not index.isValid():
            return None
        path = self._model.filePath(index)
        return path if Path(path).is_file() else None

    def _on_double_click(self, index) -> None:
        path = self._model.filePath(index)
        if Path(path).is_file():
            self.strategy_selected.emit(path)

    def _on_load_clicked(self) -> None:
        path = self._selected_path()
        if path:
            self.strategy_load_requested.emit(path)
            self._core.load_strategy(path)