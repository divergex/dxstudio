"""
dxstudio.core.commands — Terminal-style command registry and dispatcher.

Commands follow the pattern:
    VERB [ARG ...] [--option value]

Examples:
    LOAD mean_reversion.dxs
    BACKTEST 2023-01-01 2023-06-30 1000000
    SHOW RESULTS
    SESSION LIST
    HELP

Registering a custom command:
    registry = CommandRegistry()

    @registry.command("GREET")
    def greet(args, context):
        name = args[0] if args else "world"
        return f"Hello, {name}!"
"""

from __future__ import annotations

import logging
import shlex
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

CommandHandler = Callable[[List[str], Dict[str, Any]], Optional[str]]


@dataclass
class CommandSpec:
    name: str
    handler: CommandHandler
    help_text: str = ""
    usage: str = ""


class CommandRegistry:
    """
    Central registry for all dxstudio terminal commands.

    Thread-safe for read operations; registration should happen at startup.
    """

    def __init__(self) -> None:
        self._commands: Dict[str, CommandSpec] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        name: str,
        handler: CommandHandler,
        help_text: str = "",
        usage: str = "",
    ) -> None:
        key = name.upper()
        self._commands[key] = CommandSpec(
            name=key, handler=handler, help_text=help_text, usage=usage
        )
        logger.debug("Registered command: %s", key)

    def command(self, name: str, help_text: str = "", usage: str = ""):
        """Decorator form of register()."""

        def decorator(fn: CommandHandler) -> CommandHandler:
            self.register(name, fn, help_text=help_text, usage=usage)
            return fn

        return decorator

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute(self, raw: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Parse and execute a raw command string.

        Returns the string output of the handler, or an error message.
        """
        if context is None:
            context = {}

        raw = raw.strip()
        if not raw:
            return ""

        try:
            tokens = shlex.split(raw)
        except ValueError as exc:
            return f"Parse error: {exc}"

        verb = tokens[0].upper()
        args = tokens[1:]

        spec = self._commands.get(verb)
        if spec is None:
            return f"Unknown command: '{verb}'. Type HELP for a list of commands."

        try:
            result = spec.handler(args, context)
            return result or ""
        except Exception as exc:  # noqa: BLE001
            logger.exception("Command '%s' raised an exception", verb)
            return f"Error executing '{verb}': {exc}"

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def list_commands(self) -> List[CommandSpec]:
        return sorted(self._commands.values(), key=lambda s: s.name)

    def get(self, name: str) -> Optional[CommandSpec]:
        return self._commands.get(name.upper())

    # ------------------------------------------------------------------
    # Built-in: HELP
    # ------------------------------------------------------------------

    def _builtin_help(self, args: List[str], _context: Dict[str, Any]) -> str:
        if args:
            spec = self.get(args[0])
            if spec is None:
                return f"No help available for '{args[0]}'."
            lines = [f"Command : {spec.name}"]
            if spec.usage:
                lines.append(f"Usage   : {spec.usage}")
            if spec.help_text:
                lines.append(f"Help    : {spec.help_text}")
            return "\n".join(lines)

        lines = ["Available commands:", ""]
        for spec in self.list_commands():
            suffix = f"  — {spec.help_text}" if spec.help_text else ""
            lines.append(f"  {spec.name:<20}{suffix}")
        lines.append("")
        lines.append("Type HELP <command> for detailed help.")
        return "\n".join(lines)

    def install_builtins(self) -> None:
        self.register("HELP", self._builtin_help, help_text="Show available commands.", usage="HELP [command]")