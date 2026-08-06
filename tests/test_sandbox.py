from pathlib import Path

from remy.sandbox import detect
from remy.sandbox.profiles import PIP, SKILL, TOOLCHAIN, bwrap_argv, sandboxed_argv


# --- bwrap argv builder -----------------------------------------------------

def test_skill_profile_is_locked_down_no_network():
    argv = bwrap_argv(SKILL, ["python", "handler.py"], "/tmp/skills/foo")
    assert argv[0] == "bwrap"
    assert "--unshare-all" in argv
    assert "--share-net" not in argv          # profile A has no network default
    assert argv[argv.index("--tmpfs") + 1] == "/"
    assert argv[-2:] == ["python", "handler.py"]


def test_skill_can_opt_into_network():
    argv = bwrap_argv(SKILL, ["curl", "x"], "/tmp/s", network=True)
    assert "--share-net" in argv


def test_pip_profile_has_network_by_default():
    assert "--share-net" in bwrap_argv(PIP, ["pip", "install", "x"], "/tmp/venv")


def test_only_the_writable_dir_is_bound_writable():
    argv = bwrap_argv(SKILL, ["true"], "/tmp/skills/foo")
    # exactly one --bind (writable); everything else is --ro-bind-try
    assert argv.count("--bind") == 1
    assert argv[argv.index("--bind") + 1] == "/tmp/skills/foo"
    assert "--chdir" in argv


def test_secrets_and_home_are_never_mounted():
    home = str(Path.home())
    argv = bwrap_argv(SKILL, ["true"], "/tmp/skills/foo")
    joined = " ".join(argv)
    assert f"{home}/.remy" not in joined
    assert "secrets" not in joined


# --- systemd-run resource wrapper -------------------------------------------

def test_sandboxed_argv_wraps_bwrap_with_caps():
    argv = sandboxed_argv(SKILL, ["true"], "/tmp/s")
    assert argv[:4] == ["systemd-run", "--user", "--scope", "--quiet"]
    assert "MemoryMax=512M" in argv
    assert "RuntimeMaxSec=30" in argv
    # bwrap starts after the systemd `--` separator
    assert argv[argv.index("--", 4) + 1] == "bwrap"


def test_toolchain_profile_gets_the_largest_caps():
    argv = sandboxed_argv(TOOLCHAIN, ["make"], "/tmp/job")
    assert "MemoryMax=3G" in argv
    assert "RuntimeMaxSec=3600" in argv


# --- host detection (must not crash, returns bools) -------------------------

def test_sandbox_report_shape():
    rep = detect.sandbox_report()
    assert set(rep) == {"bwrap", "userns", "cgroup_v2"}
    assert all(isinstance(v, bool) for v in rep.values())


def test_detection_helpers_return_bool_offline():
    # On a box without the tools these are False; the point is they never raise.
    assert isinstance(detect.bwrap_available(), bool)
    assert isinstance(detect.userns_available(), bool)
    assert isinstance(detect.cgroup_v2_delegation(), bool)
