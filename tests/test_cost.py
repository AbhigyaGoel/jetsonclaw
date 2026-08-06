from remy.brain.claude import AgentLine, record_usage
from remy.cost import CostLedger

DAY = 86400.0
NOON = 20000 * DAY + 12 * 3600  # a fixed, realistic "now" (~2024) at midday


def ledger(tmp_path) -> CostLedger:
    return CostLedger(tmp_path / "cost.jsonl")


def test_record_and_total(tmp_path):
    led = ledger(tmp_path)
    led.record(0.12, "task one", session_id="s1", input_tokens=100,
               output_tokens=50, now=NOON)
    led.record(0.08, "task two", now=NOON)
    assert led.count() == 2
    assert abs(led.total_usd() - 0.20) < 1e-9


def test_today_excludes_yesterday(tmp_path):
    led = ledger(tmp_path)
    led.record(1.00, "old", now=NOON - DAY)   # yesterday
    led.record(0.25, "new", now=NOON)         # today
    assert abs(led.today_usd(now=NOON) - 0.25) < 1e-9
    assert abs(led.total_usd() - 1.25) < 1e-9


def test_rows_survive_reopen(tmp_path):
    ledger(tmp_path).record(0.05, "t", session_id="s", now=NOON)
    reopened = CostLedger(tmp_path / "cost.jsonl")
    rows = reopened.rows()
    assert len(rows) == 1
    assert rows[0].session_id == "s"


def test_summary_empty(tmp_path):
    assert "No agent spend" in ledger(tmp_path).summary()


# --- record_usage bridges the AgentLine result to the ledger -----------------

def test_record_usage_writes_result_line(tmp_path):
    led = ledger(tmp_path)
    line = AgentLine("result", "done", cost_usd=0.42, session_id="sess-9",
                     usage={"input_tokens": 200, "output_tokens": 80})
    record_usage(led, line, "edit the portfolio", now=NOON)
    row = led.rows()[0]
    assert row.cost_usd == 0.42
    assert row.session_id == "sess-9"
    assert row.input_tokens == 200
    assert row.task == "edit the portfolio"


def test_record_usage_noop_without_cost(tmp_path):
    led = ledger(tmp_path)
    record_usage(led, AgentLine("result", "done"), "task", now=NOON)  # no cost
    assert led.count() == 0


def test_record_usage_noop_without_ledger():
    # must not raise when there's no ledger configured
    record_usage(None, AgentLine("result", "x", cost_usd=1.0), "t")
