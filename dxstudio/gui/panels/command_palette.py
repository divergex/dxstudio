"""
dxstudio.gui.panels.command_palette — Bottom-dock terminal-style input.

Provides a single-line command input + scrollable output log.

Signals:
    command_executed(output: str)
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from dxstudio.core import StudioCore


class CommandPalettePanel(QWidget):
    command_executed = Signal(str)

    def __init__(self, core: StudioCore, parent=None) -> None:
        super().__init__(parent)
        self._core = core
        self._history: list[str] = []
        self._history_idx: int = -1
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Output log
        mono = QFont("Courier New", 9)
        self._output = QPlainTextEdit()
        self._output.setReadOnly(True)
        self._output.setFont(mono)
        self._output.setMaximumBlockCount(2000)
        self._output.setMinimumHeight(100)
        layout.addWidget(self._output)

        # Input row
        row = QHBoxLayout()
        self._prompt = QLabel("dx>")
        self._prompt.setFont(mono)
        row.addWidget(self._prompt)

        self._input = QLineEdit()
        self._input.setFont(mono)
        self._input.setPlaceholderText("Enter command… (HELP for list)")
        self._input.returnPressed.connect(self._on_submit)
        self._input.installEventFilter(self)
        row.addWidget(self._input)

        self._btn_run = QPushButton("Run")
        self._btn_run.clicked.connect(self._on_submit)
        row.addWidget(self._btn_run)

        layout.addLayout(row)

        self._append_output("dxstudio command palette ready. Type HELP for commands.")

    # ------------------------------------------------------------------

    def _on_submit(self) -> None:
        raw = self._input.text().strip()
        if not raw:
            return

        self._history.append(raw)
        self._history_idx = len(self._history)
        self._input.clear()

        self._append_output(f"dx> {raw}")
        output = self._core.run_command(raw)
        if output:
            self._append_output(output)
        self.command_executed.emit(output or "")

    def _append_output(self, text: str) -> None:
        self._output.appendPlainText(text)
        # Scroll to bottom
        sb = self._output.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ------------------------------------------------------------------
    # Arrow-key history navigation
    # ------------------------------------------------------------------

    def eventFilter(self, obj, event) -> bool:  # type: ignore[override]
        from PySide6.QtCore import QEvent
        from PySide6.QtGui import QKeyEvent

        if obj is self._input and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_Up and self._history:
                self._history_idx = max(0, self._history_idx - 1)
                self._input.setText(self._history[self._history_idx])
                return True
            if key == Qt.Key.Key_Down and self._history:
                self._history_idx = min(len(self._history), self._history_idx + 1)
                text = self._history[self._history_idx] if self._history_idx < len(self._history) else ""
                self._input.setText(text)
                return True
        return super().eventFilter(obj, event)