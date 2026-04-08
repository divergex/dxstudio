"""
dxstudio.cli.main — Command-line interface for dxstudio.

Usage:
    dxstudio run <workflow.yaml>
    dxstudio backtest <strategy.dxs> [--start START] [--end END] [--capital CAPITAL]
    dxstudio shell
    dxstudio session list
    dxstudio session new [name]
"""

from __future__ import annotations

import argparse
import sys

from ..core import StudioCore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dxstudio",
        description="dxstudio — multi-interface execution platform for quantitative strategies.",
    )
    sub = parser.add_subparsers(dest="command", metavar="command")

    # ------------------------------------------------------------------ run
    p_run = sub.add_parser("run", help="Execute a workflow YAML file.")
    p_run.add_argument("workflow", metavar="workflow.yaml", help="Path to workflow file.")

    # -------------------------------------------------------------- backtest
    p_bt = sub.add_parser("backtest", help="Run a backtest for a strategy.")
    p_bt.add_argument("strategy", metavar="strategy.dxs", help="Path to strategy file.")
    p_bt.add_argument("--start", default="2023-01-01", help="Start date (ISO-8601).")
    p_bt.add_argument("--end", default="2023-12-31", help="End date (ISO-8601).")
    p_bt.add_argument("--capital", type=float, default=1_000_000, help="Starting capital.")

    # ----------------------------------------------------------------- shell
    sub.add_parser("shell", help="Start an interactive command shell.")

    # --------------------------------------------------------------- session
    p_sess = sub.add_parser("session", help="Manage sessions.")
    sess_sub = p_sess.add_subparsers(dest="session_cmd", metavar="subcommand")
    sess_sub.add_parser("list", help="List all sessions.")
    p_sess_new = sess_sub.add_parser("new", help="Create a new session.")
    p_sess_new.add_argument("name", nargs="?", default="default", help="Session name.")

    return parser


def cmd_run(args: argparse.Namespace, core: StudioCore) -> int:
    print(f"Running workflow: {args.workflow}")
    try:
        core.execute_workflow_file(args.workflow)
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_backtest(args: argparse.Namespace, core: StudioCore) -> int:
    try:
        strategy = core.load_strategy(args.strategy)
        result = core.run_backtest(
            strategy,
            {
                "start_date": args.start,
                "end_date": args.end,
                "capital": args.capital,
                "strategy_path": args.strategy,
            },
        )
        print(result.summary())
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_shell(core: StudioCore) -> int:
    print("dxstudio interactive shell. Type HELP for commands, EXIT to quit.\n")
    while True:
        try:
            raw = input("dx> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break
        if not raw:
            continue
        if raw.upper() in {"EXIT", "QUIT", "BYE"}:
            print("Goodbye.")
            break
        output = core.run_command(raw)
        if output:
            print(output)
    return 0


def cmd_session(args: argparse.Namespace, core: StudioCore) -> int:
    sub = getattr(args, "session_cmd", None)
    if sub == "list" or sub is None:
        sessions = core.list_sessions()
        for s in sessions:
            marker = "* " if s.id == core.active_session.id else "  "
            print(f"{marker}{s.name} [{s.id[:8]}]")
    elif sub == "new":
        s = core.new_session(args.name)
        print(f"Created session: {s.name} [{s.id[:8]}]")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    core = StudioCore()

    dispatch = {
        "run": lambda: cmd_run(args, core),
        "backtest": lambda: cmd_backtest(args, core),
        "shell": lambda: cmd_shell(core),
        "session": lambda: cmd_session(args, core),
    }

    fn = dispatch.get(args.command)
    if fn is None:
        parser.print_help()
        return 1
    return fn()


if __name__ == "__main__":
    sys.exit(main())