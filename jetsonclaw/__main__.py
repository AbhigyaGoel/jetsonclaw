"""Entry point: `python -m jetsonclaw [--headless] [--selftest] [--config PATH]`

Import discipline matters here: the boot guard must run before importing the
rest of the package, so a broken self-iteration can be auto-reverted even when
it breaks imports elsewhere.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
STATE_DIR = "~/.jetsonclaw"


def selftest() -> int:
    """Import every package module, then run the unit tests. This is the gate
    every self-iteration must pass before its change is committed."""
    import importlib
    import pkgutil

    import jetsonclaw

    failures = []
    for info in pkgutil.walk_packages(jetsonclaw.__path__, prefix="jetsonclaw."):
        try:
            importlib.import_module(info.name)
        except Exception as e:
            failures.append(f"{info.name}: {type(e).__name__}: {e}")
    if failures:
        print("IMPORT FAILURES:\n" + "\n".join(failures))
        return 1

    import pytest

    tests_dir = REPO_DIR / "tests"
    if tests_dir.is_dir():
        return pytest.main(["-q", "-x", str(tests_dir)])
    print("selftest: imports OK (no tests dir)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="jetsonclaw")
    parser.add_argument("--selftest", action="store_true",
                        help="import all modules and run tests, then exit")
    parser.add_argument("--doctor", action="store_true",
                        help="diagnose mic/speaker/ollama/claude setup, then exit")
    parser.add_argument("--headless", action="store_true",
                        help="plain console output instead of the TUI")
    parser.add_argument("--config", default=None, help="path to config.toml")
    args = parser.parse_args(argv)

    if args.selftest:
        return selftest()

    if args.doctor:
        from jetsonclaw.config import load_config
        from jetsonclaw.diagnostics import run_doctor
        return run_doctor(load_config(args.config))

    # Boot guard BEFORE importing anything an agent might have broken.
    from jetsonclaw.supervisor import BootGuard, restart_in_place

    guard = BootGuard(STATE_DIR, REPO_DIR)
    guard.mark_boot()
    if guard.crash_looping():
        ref = guard.revert_to_last_good()
        if ref:
            print(f"!! crash loop detected — reverted to last good commit {ref[:8]}")
            restart_in_place()
        print("!! crash loop detected and no last-good ref recorded; continuing anyway")

    from jetsonclaw.config import load_config
    from jetsonclaw.runner import run_headless, run_tui

    cfg = load_config(args.config)
    if args.headless:
        return run_headless(cfg, guard, REPO_DIR)
    return run_tui(cfg, guard, REPO_DIR)


if __name__ == "__main__":
    sys.exit(main())
