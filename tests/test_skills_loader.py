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
