"""
dxstudio.core.workflow — Declarative, serializable workflow pipelines.

Workflows are defined in YAML and consist of ordered steps. Each step
maps to a registered handler in WorkflowEngine. Steps are executed
sequentially; the output of each step is passed as context to the next.

Example YAML:
    steps:
      - type: load_strategy
        path: mean_reversion.dxs

      - type: backtest
        start_date: 2023-01-01
        end_date: 2023-06-30
        capital: 1000000

      - type: display_results
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class WorkflowStep:
    """A single step inside a workflow."""

    type: str
    params: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowStep":
        step_type = data.pop("type")
        return cls(type=step_type, params=data)

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.type, **self.params}


@dataclass
class Workflow:
    """An ordered collection of WorkflowSteps."""

    name: str = "unnamed"
    steps: List[WorkflowStep] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "metadata": self.metadata,
            "steps": [s.to_dict() for s in self.steps],
        }

    def to_yaml(self) -> str:
        return yaml.dump(self.to_dict(), default_flow_style=False)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(self.to_yaml(), encoding="utf-8")
        logger.info("Workflow saved to %s", path)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Workflow":
        steps_raw = data.get("steps", [])
        steps = [WorkflowStep.from_dict(dict(s)) for s in steps_raw]
        return cls(
            name=data.get("name", "unnamed"),
            steps=steps,
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def load(cls, path: str | Path) -> "Workflow":
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        workflow = cls.from_dict(raw)
        logger.info("Workflow loaded from %s (%d steps)", path, len(workflow.steps))
        return workflow


# ---------------------------------------------------------------------------
# Execution engine
# ---------------------------------------------------------------------------

StepHandler = Callable[[Dict[str, Any], Dict[str, Any]], Optional[Dict[str, Any]]]


class WorkflowEngine:
    """
    Executes Workflow objects by dispatching each step to a registered handler.

    Handlers receive (params, context) and may return a dict that is merged
    into the shared context for subsequent steps.

    Usage:
        engine = WorkflowEngine()
        engine.register("load_strategy", my_load_handler)
        engine.register("backtest", my_backtest_handler)
        result_context = engine.run(workflow)
    """

    def __init__(self) -> None:
        self._handlers: Dict[str, StepHandler] = {}

    def register(self, step_type: str, handler: StepHandler) -> None:
        """Register a handler for a step type."""
        self._handlers[step_type] = handler
        logger.debug("Registered workflow step handler: %s", step_type)

    def run(self, workflow: Workflow) -> Dict[str, Any]:
        """
        Execute all steps in order.

        Returns the final accumulated context dict.
        """
        context: Dict[str, Any] = {}
        logger.info("Starting workflow '%s' (%d steps)", workflow.name, len(workflow.steps))

        for i, step in enumerate(workflow.steps):
            handler = self._handlers.get(step.type)
            if handler is None:
                raise ValueError(
                    f"No handler registered for step type '{step.type}' "
                    f"(step {i + 1}/{len(workflow.steps)})."
                )

            logger.info("  [%d/%d] %s", i + 1, len(workflow.steps), step.type)
            result = handler(step.params, context)
            if result:
                context.update(result)

        logger.info("Workflow '%s' completed.", workflow.name)
        return context