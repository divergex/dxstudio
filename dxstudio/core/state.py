"""
dxstudio.core.state — Session and application state management.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class BacktestResult:
    """Holds the result of a single backtest run."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    strategy_path: str = ""
    start_date: str = ""
    end_date: str = ""
    capital: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Populated by dxlib after execution
    metrics: Dict[str, Any] = field(default_factory=dict)
    equity_curve: List[float] = field(default_factory=list)
    trades: List[Dict[str, Any]] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"Backtest Result [{self.id[:8]}]",
            f"  Strategy : {self.strategy_path}",
            f"  Period   : {self.start_date} → {self.end_date}",
            f"  Capital  : {self.capital:,.0f}",
        ]
        for k, v in self.metrics.items():
            lines.append(f"  {k:<12}: {v}")
        return "\n".join(lines)


@dataclass
class Session:
    """Represents a single working session."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "default"
    created_at: datetime = field(default_factory=datetime.utcnow)

    loaded_strategies: List[str] = field(default_factory=list)
    results: List[BacktestResult] = field(default_factory=list)

    def add_result(self, result: BacktestResult) -> None:
        self.results.append(result)

    def last_result(self) -> Optional[BacktestResult]:
        return self.results[-1] if self.results else None


class StateManager:
    """
    Central state store for dxstudio.

    Holds active sessions and the current session pointer.
    All interfaces (API, CLI, GUI) share one StateManager instance
    via StudioCore.
    """

    def __init__(self) -> None:
        self._sessions: Dict[str, Session] = {}
        self._active_session: Optional[Session] = None
        self.new_session()  # always start with one session

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    def new_session(self, name: str = "default") -> Session:
        session = Session(name=name)
        self._sessions[session.id] = session
        self._active_session = session
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)

    def list_sessions(self) -> List[Session]:
        return list(self._sessions.values())

    @property
    def active_session(self) -> Session:
        if self._active_session is None:
            self.new_session()
        return self._active_session  # type: ignore[return-value]

    def switch_session(self, session_id: str) -> Session:
        session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"Session '{session_id}' not found.")
        self._active_session = session
        return session

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def record_result(self, result: BacktestResult) -> None:
        self.active_session.add_result(result)

    def record_strategy(self, path: str) -> None:
        if path not in self.active_session.loaded_strategies:
            self.active_session.loaded_strategies.append(path)