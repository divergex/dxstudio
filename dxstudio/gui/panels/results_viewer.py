"""
dxstudio.gui.panels.results_viewer — Central panel showing backtest results.

Displays:
    - Metrics table (key/value)
    - Equity curve (simple QChart placeholder; swap for your preferred chart lib)
    - Trades table
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from dxstudio.core import StudioCore, BacktestResult


class MetricsTable(QTableWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(0, 2, parent)
        self.setHorizontalHeaderLabels(["Metric", "Value"])
        self.horizontalHeader().setStretchLastSection(True)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

    def load(self, metrics: dict) -> None:
        self.setRowCount(0)
        for key, value in metrics.items():
            row = self.rowCount()
            self.insertRow(row)
            self.setItem(row, 0, QTableWidgetItem(str(key)))
            self.setItem(row, 1, QTableWidgetItem(str(value)))


class TradesTable(QTableWidget):
    COLUMNS = ["Date", "Symbol", "Side", "Quantity", "Price", "P&L"]

    def __init__(self, parent=None) -> None:
        super().__init__(0, len(self.COLUMNS), parent)
        self.setHorizontalHeaderLabels(self.COLUMNS)
        self.horizontalHeader().setStretchLastSection(True)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

    def load(self, trades: list) -> None:
        self.setRowCount(0)
        for trade in trades:
            row = self.rowCount()
            self.insertRow(row)
            for col, key in enumerate(["date", "symbol", "side", "quantity", "price", "pnl"]):
                self.setItem(row, col, QTableWidgetItem(str(trade.get(key, ""))))


class ResultsViewerPanel(QWidget):
    def __init__(self, core: StudioCore, parent=None) -> None:
        super().__init__(parent)
        self._core = core
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        self._label = QLabel("No results yet. Run a backtest to see results here.")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label)

        self._splitter = QSplitter(Qt.Orientation.Vertical)

        # Metrics
        metrics_container = QWidget()
        m_layout = QVBoxLayout(metrics_container)
        m_layout.addWidget(QLabel("<b>Metrics</b>"))
        self._metrics_table = MetricsTable()
        m_layout.addWidget(self._metrics_table)
        self._splitter.addWidget(metrics_container)

        # Equity curve placeholder
        self._equity_label = QLabel("Equity curve will render here (integrate your chart library).")
        self._equity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._equity_label.setMinimumHeight(200)
        self._equity_label.setStyleSheet("border: 1px dashed #aaa; color: #888;")
        self._splitter.addWidget(self._equity_label)

        # Trades
        trades_container = QWidget()
        t_layout = QVBoxLayout(trades_container)
        t_layout.addWidget(QLabel("<b>Trades</b>"))
        self._trades_table = TradesTable()
        t_layout.addWidget(self._trades_table)
        self._splitter.addWidget(trades_container)

        layout.addWidget(self._splitter)
        self._splitter.hide()

    def refresh(self) -> None:
        """Pull the latest result from the active session and display it."""
        result = self._core.active_session.last_result()
        if result is None:
            return
        self._show_result(result)

    def _show_result(self, result: BacktestResult) -> None:
        self._label.hide()
        self._splitter.show()
        self._metrics_table.load(result.metrics)
        self._trades_table.load(result.trades)
        if result.equity_curve:
            self._equity_label.setText(f"Equity curve: {len(result.equity_curve)} data points (render with your chart lib)")