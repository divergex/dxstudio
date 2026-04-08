"""
dxstudio.core.studio — StudioCore, the central orchestration layer.

All interfaces (API, CLI, GUI) talk exclusively to StudioCore.
StudioCore owns:
  - StateManager     (sessions, results)
  - WorkflowEngine   (pipeline execution)
  - CommandRegistry  (terminal commands)

It does NOT import dxlib directly; instead it delegates to pluggable
adapters so that dxlib can be swapped, mocked, or upgraded independently.

Adapters are simple callables or objects set via:
    core.set_strategy_loader(fn)
    core.set_backtest_runner(fn)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .commands import CommandRegistry
from .state import BacktestResult, Session, StateManager
from .workflow import Workflow, WorkflowEngine

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Stub adapters (replace with real dxlib calls)
# ---------------------------------------------------------------------------

def _default_strategy_loader(path: str) -> Any:
    """Replace with: from dxlib import load_strategy; return load_strategy(path)"""
    logger.warning("No strategy loader configured. Using stub for '%s'.", path)
    return {"path": path, "_stub": True}


def _default_backtest_runner(strategy: Any, config: Dict[str, Any]) -> BacktestResult:
    """Replace with real dxlib backtest call."""
    logger.warning("No backtest runner configured. Returning stub result.")
    return BacktestResult(
        strategy_path=config.get("strategy_path", ""),
        start_date=config.get("start_date", ""),
        end_date=config.get("end_date", ""),
        capital=config.get("capital", 0.0),
        metrics={"_stub": True},
    )


# ---------------------------------------------------------------------------
# StudioCore
# ---------------------------------------------------------------------------


class StudioCore:
    """
    Central coordination layer for dxstudio.

    One instance is created per application lifetime and shared across
    all interface layers.
    """

    def __init__(self) -> None:
        self.state = StateManager()
        self.workflow_engine = WorkflowEngine()
        self.commands = CommandRegistry()

        # Pluggable adapters
        self._strategy_loader: Callable[[str], Any] = _default_strategy_loader
        self._backtest_runner: Callable[[Any, Dict[str, Any]], BacktestResult] = _default_backtest_runner

        self._setup_commands()
        self._setup_workflow_steps()

    # ------------------------------------------------------------------
    # Adapter injection
    # ------------------------------------------------------------------

    def set_strategy_loader(self, fn: Callable[[str], Any]) -> None:
        """Inject a real dxlib strategy loader."""
        self._strategy_loader = fn

    def set_backtest_runner(self, fn: Callable[[Any, Dict[str, Any]], BacktestResult]) -> None:
        """Inject a real dxlib backtest runner."""
        self._backtest_runner = fn

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def load_strategy(self, path: str) -> Any:
        """Load a strategy file and record it in the active session."""
        resolved = str(Path(path).resolve())
        logger.info("Loading strategy: %s", resolved)
        strategy = self._strategy_loader(resolved)
        self.state.record_strategy(resolved)
        return strategy

    def run_backtest(self, strategy: Any, config: Dict[str, Any]) -> BacktestResult:
        """Execute a backtest and store the result."""
        logger.info(
            "Running backtest: %s → %s, capital=%.0f",
            config.get("start_date"),
            config.get("end_date"),
            config.get("capital", 0),
        )
        result = self._backtest_runner(strategy, config)
        self.state.record_result(result)
        return result

    def display_results(self, result: Optional[BacktestResult] = None) -> str:
        """
        Return a text summary of a result (or the last recorded one).

        The GUI/CLI can display this however they like.
        """
        target = result or self.state.active_session.last_result()
        if target is None:
            return "No results available."
        return target.summary()

    # ------------------------------------------------------------------
    # Workflow execution
    # ------------------------------------------------------------------

    def execute_workflow(self, workflow: Workflow) -> Dict[str, Any]:
        return self.workflow_engine.run(workflow)

    def execute_workflow_file(self, path: str) -> Dict[str, Any]:
        workflow = Workflow.load(path)
        return self.execute_workflow(workflow)

    # ------------------------------------------------------------------
    # Command execution
    # ------------------------------------------------------------------

    def run_command(self, raw: str) -> str:
        context = {"core": self, "session": self.state.active_session}
        return self.commands.execute(raw, context)

    # ------------------------------------------------------------------
    # Session management (pass-through for convenience)
    # ------------------------------------------------------------------

    @property
    def active_session(self) -> Session:
        return self.state.active_session

    def list_sessions(self) -> List[Session]:
        return self.state.list_sessions()

    def new_session(self, name: str = "default") -> Session:
        return self.state.new_session(name)

    def switch_session(self, session_id: str) -> Session:
        return self.state.switch_session(session_id)

    # ------------------------------------------------------------------
    # Internal: wire up built-in commands
    # ------------------------------------------------------------------

    def _setup_commands(self) -> None:
        reg = self.commands
        reg.install_builtins()

        @reg.command("LOAD", help_text="Load a strategy file.", usage="LOAD <path>")
        def cmd_load(args: List[str], ctx: Dict[str, Any]) -> str:
            if not args:
                return "Usage: LOAD <path>"
            core: StudioCore = ctx["core"]
            strategy = core.load_strategy(args[0])
            ctx["strategy"] = strategy
            return f"Strategy loaded: {args[0]}"

        @reg.command(
            "BACKTEST",
            help_text="Run a backtest for a date range.",
            usage="BACKTEST <start_date> <end_date> <capital>",
        )
        def cmd_backtest(args: List[str], ctx: Dict[str, Any]) -> str:
            if len(args) < 3:
                return "Usage: BACKTEST <start_date> <end_date> <capital>"
            core: StudioCore = ctx["core"]
            strategy = ctx.get("strategy")
            if strategy is None:
                return "No strategy loaded. Run LOAD first."
            config = {
                "start_date": args[0],
                "end_date": args[1],
                "capital": float(args[2]),
                "strategy_path": getattr(strategy, "path", str(strategy)),
            }
            result = core.run_backtest(strategy, config)
            ctx["last_result"] = result
            return f"Backtest complete. Result ID: {result.id[:8]}"

        @reg.command("SHOW", help_text="Show results or session info.", usage="SHOW RESULTS | SHOW SESSION")
        def cmd_show(args: List[str], ctx: Dict[str, Any]) -> str:
            core: StudioCore = ctx["core"]
            sub = args[0].upper() if args else "RESULTS"
            if sub == "RESULTS":
                return core.display_results()
            if sub == "SESSION":
                s = core.active_session
                lines = [
                    f"Session  : {s.name} [{s.id[:8]}]",
                    f"Created  : {s.created_at.isoformat()}",
                    f"Strategies loaded : {len(s.loaded_strategies)}",
                    f"Results           : {len(s.results)}",
                ]
                return "\n".join(lines)
            return f"Unknown subcommand: {sub}"

        @reg.command("SESSION", help_text="Manage sessions.", usage="SESSION LIST | SESSION NEW [name] | SESSION SWITCH <id>")
        def cmd_session(args: List[str], ctx: Dict[str, Any]) -> str:
            core: StudioCore = ctx["core"]
            sub = args[0].upper() if args else "LIST"
            if sub == "LIST":
                sessions = core.list_sessions()
                lines = []
                for s in sessions:
                    marker = "* " if s.id == core.active_session.id else "  "
                    lines.append(f"{marker}{s.name} [{s.id[:8]}] — {len(s.results)} results")
                return "\n".join(lines) if lines else "No sessions."
            if sub == "NEW":
                name = args[1] if len(args) > 1 else "default"
                s = core.new_session(name)
                return f"New session created: {s.name} [{s.id[:8]}]"
            if sub == "SWITCH":
                if len(args) < 2:
                    return "Usage: SESSION SWITCH <id>"
                s = core.switch_session(args[1])
                return f"Switched to session: {s.name} [{s.id[:8]}]"
            return f"Unknown SESSION subcommand: {sub}"

    # ------------------------------------------------------------------
    # Internal: wire up built-in workflow step handlers
    # ------------------------------------------------------------------

    def _setup_workflow_steps(self) -> None:
        engine = self.workflow_engine

        def step_load_strategy(params: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
            strategy = self.load_strategy(params["path"])
            return {"strategy": strategy}

        def step_backtest(params: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
            strategy = ctx.get("strategy")
            if strategy is None:
                raise RuntimeError("No strategy in context. Add a load_strategy step first.")
            result = self.run_backtest(strategy, params)
            return {"last_result": result}

        def step_display_results(params: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
            result = ctx.get("last_result")
            print(self.display_results(result))
            return {}

        engine.register("load_strategy", step_load_strategy)
        engine.register("backtest", step_backtest)
        engine.register("display_results", step_display_results)