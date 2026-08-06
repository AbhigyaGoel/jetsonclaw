"""Cost ledger: measure what agent sessions actually cost, don't guess.

REMY is on the owner's Claude subscription today, so this costs nothing to run —
which is exactly why it should run now. The `result` line of every agent session
carries `total_cost_usd` and `usage`; we persist one row per session so that
"what would a 30-minute job cost" is answered with real numbers, and so the
overseer can enforce budgets later. See the billing constraint in CLAUDE.md.

Append-only JSONL (same shape as episodic memory), no dependency.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class CostRow:
    ts: float
    session_id: str
    cost_usd: float
    input_tokens: int
    output_tokens: int
    task: str


class CostLedger:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).expanduser()

    def record(self, cost_usd: float, task: str, *, session_id: str = "",
               input_tokens: int = 0, output_tokens: int = 0,
               now: float | None = None) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        row = {
            "ts": time.time() if now is None else now,
            "session_id": session_id,
            "cost_usd": float(cost_usd),
            "input_tokens": int(input_tokens),
            "output_tokens": int(output_tokens),
            "task": task[:120],
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def rows(self) -> list[CostRow]:
        if not self.path.is_file():
            return []
        out = []
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                try:
                    d = json.loads(line)
                    out.append(CostRow(d["ts"], d.get("session_id", ""),
                                       d["cost_usd"], d.get("input_tokens", 0),
                                       d.get("output_tokens", 0),
                                       d.get("task", "")))
                except (json.JSONDecodeError, KeyError):
                    continue
        return out

    def total_usd(self) -> float:
        return sum(r.cost_usd for r in self.rows())

    def since(self, ts: float) -> float:
        return sum(r.cost_usd for r in self.rows() if r.ts >= ts)

    def today_usd(self, now: float | None = None) -> float:
        now = time.time() if now is None else now
        start = datetime.fromtimestamp(now).replace(
            hour=0, minute=0, second=0, microsecond=0).timestamp()
        return self.since(start)

    def count(self) -> int:
        return len(self.rows())

    def summary(self, now: float | None = None) -> str:
        """One line for the status report: sessions, today, all-time."""
        rows = self.rows()
        if not rows:
            return "No agent spend recorded yet."
        return (f"{len(rows)} agent sessions, "
                f"${self.today_usd(now):.2f} today, "
                f"${self.total_usd():.2f} all time.")
