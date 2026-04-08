"""
dxstudio.api.studio_api — Public programmatic interface for dxstudio.

This is the primary entry-point for scripting and automation.

Example:
    from dxstudio import Studio

    studio = Studio()
    strategy = studio.load_strategy("mean_reversion.dxs")
    results = studio.backtest(
        strategy,
        start_date="2023-01-01",
        end_date="2023-06-30",
        capital=1_000_000,
    )
    studio.display_results(results)
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from ..core import BacktestResult, Session, StudioCore, Workflow


class Studio:
    """
    High-level façade over StudioCore.

    Provides a clean, stable public API that insulates callers from
    internal implementation details.
    """

    def __init__(self) -> None:
        self._core = StudioCore()

    # ------------------------------------------------------------------
    # Adapter injection (connect to dxlib)
    # ------------------------------------------------------------------

    def set_strategy_loader(self, fn: Callable[[str], Any]) -> "Studio":
        """
        Inject a custom strategy loader (e.g. dxlib's load_strategy).

        Returns self for chaining.
        """
        self._core.set_strategy_loader(fn)
        return self

    def set_backtest_runner(self, fn: Callable[[Any, Dict[str, Any]], BacktestResult]) -> "Studio":
        """
        Inject a custom backtest runner (e.g. dxlib's run_backtest).

        Returns self for chaining.
        """
        self._core.set_backtest_runner(fn)
        return self

    # ------------------------------------------------------------------
    # Strategy
    # ------------------------------------------------------------------

    def load_strategy(self, path: str) -> Any:
        """Load a strategy file and return the strategy object."""
        return self._core.load_strategy(path)

    # ------------------------------------------------------------------
    # Backtesting
    # ------------------------------------------------------------------

    def backtest(
        self,
        strategy: Any,
        *,
        start_date: str,
        end_date: str,
        capital: float,
        **extra_config: Any,
    ) -> BacktestResult:
        """
        Run a backtest for the given strategy and date range.

        Args:
            strategy: Strategy object returned by load_strategy().
            start_date: ISO-8601 start date, e.g. "2023-01-01".
            end_date: ISO-8601 end date, e.g. "2023-06-30".
            capital: Starting capital.
            **extra_config: Additional parameters forwarded to the runner.

        Returns:
            BacktestResult with metrics, equity curve, and trades.
        """
        config = {
            "start_date": start_date,
            "end_date": end_date,
            "capital": capital,
            "strategy_path": getattr(strategy, "path", str(strategy)),
            **extra_config,
        }
        return self._core.run_backtest(strategy, config)

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------

    def display_results(self, result: Optional[BacktestResult] = None) -> str:
        """
        Print and return a human-readable summary of a BacktestResult.

        If result is None, uses the most recent result in the active session.
        """
        summary = self._core.display_results(result)
        print(summary)
        return summary

    # ------------------------------------------------------------------
    # Workflows
    # ------------------------------------------------------------------

    def run_workflow(self, path: str) -> Dict[str, Any]:
        """Execute a workflow defined in a YAML file."""
        return self._core.execute_workflow_file(path)

    def run_workflow_object(self, workflow: Workflow) -> Dict[str, Any]:
        """Execute a Workflow object directly."""
        return self._core.execute_workflow(workflow)

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def run_command(self, command: str) -> str:
        """Execute a single command string and return the output."""
        return self._core.run_command(command)

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------

    @property
    def session(self) -> Session:
        """The currently active session."""
        return self._core.active_session

    def new_session(self, name: str = "default") -> Session:
        return self._core.new_session(name)

    def list_sessions(self) -> List[Session]:
        return self._core.list_sessions()

    # ------------------------------------------------------------------
    # Internal access (for power users / testing)
    # ------------------------------------------------------------------

    @property
    def core(self) -> StudioCore:
        """Direct access to StudioCore (use sparingly)."""
        return self._core