"""
dxstudio.gui.panels.workflow_editor — Right-dock visual workflow editor.

The editor provides a simple YAML text area so users can author workflows
directly. A "Run" button fires the workflow_run_requested signal.

For a richer drag-and-drop node editor, replace the QPlainTextEdit with
a node graph widget (e.g. Qt Node Editor or a custom scene/view).

Signals:
    workflow_run_requested(yaml_text: str)
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from dxstudio.core import StudioCore, Workflow

_EXAMPLE_WORKFLOW = """\
# Example workflow — customize as needed
name: my_workflow

steps:
  - type: load_strategy
    path: mean_reversion.dxs

  - type: backtest
    start_date: "2023-01-01"
    end_date: "2023-06-30"
    capital: 1000000

  - type: display_results
"""


class WorkflowEditorPanel(QWidget):
    workflow_run_requested = Signal(str)

    def __init__(self, core: StudioCore, parent=None) -> None:
        super().__init__(parent)
        self._core = core
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(QLabel("<b>Workflow (YAML)</b>"))

        self._editor = QPlainTextEdit()
        self._editor.setPlainText(_EXAMPLE_WORKFLOW)
        self._editor.setMinimumWidth(260)
        layout.addWidget(self._editor)

        btn_row = QHBoxLayout()
        self._btn_run = QPushButton("▶  Run Workflow")
        self._btn_run.clicked.connect(self._on_run)
        btn_row.addWidget(self._btn_run)

        self._btn_validate = QPushButton("✓ Validate")
        self._btn_validate.clicked.connect(self._on_validate)
        btn_row.addWidget(self._btn_validate)

        layout.addLayout(btn_row)

    def _on_run(self) -> None:
        yaml_text = self._editor.toPlainText()
        self.workflow_run_requested.emit(yaml_text)

    def _on_validate(self) -> None:
        yaml_text = self._editor.toPlainText()
        try:
            import yaml
            data = yaml.safe_load(yaml_text)
            Workflow.from_dict(data)
            QMessageBox.information(self, "Validation", "Workflow is valid ✓")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Validation Error", str(exc))

    def get_workflow_yaml(self) -> str:
        return self._editor.toPlainText()

    def set_workflow_yaml(self, yaml_text: str) -> None:
        self._editor.setPlainText(yaml_text)