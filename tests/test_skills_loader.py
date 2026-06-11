import sys
import textwrap
from pathlib import Path

import pytest

from jetsonclaw.skills.loader import SkillLoader, parse_skill


def write_skill(root: Path, name: str, body: str) -> Path:
    d = root / name
    d.mkdir(parents=True)
    path = d / "SKILL.md"
    path.write_text(textwrap.dedent(body), encoding="utf-8")
    return path


def test_parse_command_skill(tmp_path: Path):
    path = write_skill(tmp_path, "greet", """\
        ---
        name: greet
        description: say hi
        triggers:
          - say hi
        action:
          command: echo hello from skill
        ---
        notes
        """)
    skill = parse_skill(path)
    assert skill is not None
    assert skill.name == "greet"
    assert skill.matches("hey jarvis say hi please")
    assert not skill.matches("play music")


@pytest.mark.skipif(sys.platform == "win32", reason="command skills run via bash")
def test_command_skill_runs(tmp_path: Path):
    write_skill(tmp_path, "greet", """\
        ---
        name: greet
        description: say hi
        triggers: [say hi]
        action:
          command: echo "hello $JARVIS_TEXT"
        ---
        """)
    skill = SkillLoader(tmp_path).find("say hi")
    assert skill.run("say hi") == "hello say hi"


def test_script_skill_runs(tmp_path: Path):
    d = tmp_path / "adder"
    d.mkdir()
    (d / "SKILL.md").write_text(textwrap.dedent("""\
        ---
        name: adder
        description: adds
        triggers: [add numbers]
        action:
          script: handler.py
        ---
        """), encoding="utf-8")
    (d / "handler.py").write_text("def handle(text):\n    return 'sum is 42'\n")
    skill = SkillLoader(tmp_path).find("add numbers now")
    assert skill.run("add numbers now") == "sum is 42"


def test_missing_required_bin_hides_skill(tmp_path: Path):
    write_skill(tmp_path, "ghost", """\
        ---
        name: ghost
        description: needs a missing binary
        triggers: [ghost command]
        action:
          command: definitely-not-a-real-binary-xyz
        requires:
          bins: [definitely-not-a-real-binary-xyz]
        ---
        """)
    assert SkillLoader(tmp_path).find("ghost command") is None


def test_invalid_frontmatter_ignored(tmp_path: Path):
    write_skill(tmp_path, "broken", "no frontmatter at all\n")
    write_skill(tmp_path, "noname", "---\ndescription: x\ntriggers: [y]\n---\n")
    assert SkillLoader(tmp_path).scan() == []


def test_hot_reload_on_mtime_change(tmp_path: Path):
    path = write_skill(tmp_path, "evolving", """\
        ---
        name: evolving
        description: v1
        triggers: [old phrase]
        action: {command: echo v1}
        ---
        """)
    loader = SkillLoader(tmp_path)
    assert loader.find("old phrase") is not None
    path.write_text(textwrap.dedent("""\
        ---
        name: evolving
        description: v2
        triggers: [new phrase]
        action: {command: echo v2}
        ---
        """), encoding="utf-8")
    import os
    os.utime(path, (path.stat().st_atime, path.stat().st_mtime + 10))
    assert loader.find("old phrase") is None
    assert loader.find("new phrase") is not None


def test_catalog_lists_skills(tmp_path: Path):
    write_skill(tmp_path, "greet", """\
        ---
        name: greet
        description: say hi
        triggers: [say hi]
        action: {command: echo hi}
        ---
        """)
    assert "greet: say hi" in SkillLoader(tmp_path).catalog()


def test_watch_skill_parses_interval(tmp_path: Path):
    write_skill(tmp_path, "ci", """\
        ---
        name: ci
        description: watch ci
        watch:
          interval_secs: 300
        action: {command: echo ok}
        ---
        """)
    watchers = SkillLoader(tmp_path).watchers()
    assert len(watchers) == 1
    assert watchers[0].watch_interval == 300.0


def test_watch_interval_floor_is_60s(tmp_path: Path):
    write_skill(tmp_path, "spam", """\
        ---
        name: spam
        description: too eager
        watch: 5
        action: {command: echo hi}
        ---
        """)
    assert SkillLoader(tmp_path).watchers()[0].watch_interval == 60.0


def test_watch_only_skill_needs_no_triggers(tmp_path: Path):
    write_skill(tmp_path, "quiet", """\
        ---
        name: quiet
        description: schedule only
        watch: 600
        action: {command: echo hi}
        ---
        """)
    loader = SkillLoader(tmp_path)
    assert loader.find("quiet") is None      # no voice trigger
    assert len(loader.watchers()) == 1


def test_skill_with_neither_trigger_nor_watch_rejected(tmp_path: Path):
    write_skill(tmp_path, "inert", """\
        ---
        name: inert
        description: does nothing
        action: {command: echo hi}
        ---
        """)
    assert SkillLoader(tmp_path).scan() == []


def test_missing_env_hides_skill(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("TOTALLY_UNSET_VAR_X", raising=False)
    write_skill(tmp_path, "needskey", """\
        ---
        name: needskey
        description: needs an api key
        triggers: [secret thing]
        action: {command: echo hi}
        requires:
          env: [TOTALLY_UNSET_VAR_X]
        ---
        """)
    assert SkillLoader(tmp_path).find("secret thing") is None
    monkeypatch.setenv("TOTALLY_UNSET_VAR_X", "value")
    loader2 = SkillLoader(tmp_path)
    assert loader2.find("secret thing") is not None


def test_inject_only_knowledge_skill(tmp_path: Path):
    d = tmp_path / "lore"
    d.mkdir()
    (d / "SKILL.md").write_text(textwrap.dedent("""\
        ---
        name: lore
        description: house facts
        inject: [thermostat, heating]
        ---
        The thermostat is in the hallway. Never set it above 23C.
        """), encoding="utf-8")
    loader = SkillLoader(tmp_path)
    assert loader.find("thermostat") is None  # no action, not routable
    assert "hallway" in loader.knowledge_for("what's up with the thermostat")
    assert loader.knowledge_for("play some jazz") == ""


def test_converse_followup(tmp_path: Path):
    d = tmp_path / "quiz"
    d.mkdir()
    (d / "SKILL.md").write_text(textwrap.dedent("""\
        ---
        name: quiz
        description: a quiz game
        triggers: [start a quiz]
        action: {script: handler.py}
        ---
        """), encoding="utf-8")
    (d / "handler.py").write_text(textwrap.dedent("""\
        def handle(text):
            return "Question one: what is 2 plus 2?"

        def converse(text):
            if "4" in text or "four" in text.lower():
                return "Correct."
            if "stop" in text.lower():
                return None
            return "Nope, try again."
        """))
    skill = SkillLoader(tmp_path).by_name("quiz")
    assert skill.converse("it's four") == "Correct."
    assert skill.converse("stop the quiz") is None  # declines, falls through


def test_converse_absent_returns_none(tmp_path: Path):
    write_skill(tmp_path, "plain", """\
        ---
        name: plain
        description: command skill
        triggers: [plain thing]
        action: {command: echo hi}
        ---
        """)
    assert SkillLoader(tmp_path).by_name("plain").converse("anything") is None
