# containers/bubblewrap — DEPEND (primary sandbox, wrap the binary)

Unprivileged sandbox via Linux user namespaces. Builds a fresh mount namespace
whose root is an invisible tmpfs; everything the child can see is an explicit
`--ro-bind`/`--bind`. This is REMY's primary containment mechanism for skill
`action.command`, out-of-process `action.script`, and pip installs. Available
as apt package `bubblewrap 0.6.1-1ubuntu0.1` on jammy arm64 (44KB pkg).

- **Stars/health:** 8.3k, active (2026-06) · **License:** LGPL-2.0-or-later
  (wrapping the binary is fine; do not statically link the C)

## Does better than REMY
REMY's skill runner (`subprocess.run(["bash","-c",cmd])` with a trimmed PATH)
is policy, not a boundary. bwrap gives a kernel boundary: unlisted paths do not
exist inside the sandbox, `PR_SET_NO_NEW_PRIVS` kills setuid escapes, and
`--unshare-all` drops net/pid/ipc/uts/user namespaces. No root, no VM, no
daemon.

## Read these files
- `containers/bubblewrap@2f55bae:README.md:L12-22` — unprivileged-userns model;
  the setuid fallback mode has been REMOVED at HEAD (jammy's 0.6.1 package is
  built non-setuid and needs kernel userns; if userns is off on the Jetson
  kernel there is no setuid escape hatch in a modern bwrap).
- `containers/bubblewrap@2f55bae:README.md:L41-63` — "not a complete,
  ready-made sandbox": the caller owns the security model; REMY must own its
  profile definitions.
- `containers/bubblewrap@2f55bae:README.md:L98-118` — empty-tmpfs-root model
  and the canonical `--ro-bind /usr ... --proc /proc --dev /dev --unshare-pid`
  invocation.

## Lift: the three REMY profiles (bwrap 0.6.1-compatible flags only)

bwrap has no resource limits; wrap it in a `systemd-run --user --scope` for
cgroup memory/pids/wallclock (see systemd notes in the research summary).

Profile A, run a synthesized skill (Python or shell):

```
systemd-run --user --scope --collect -q \
  -p MemoryMax=512M -p TasksMax=64 -p RuntimeMaxSec=30 \
  bwrap \
    --die-with-parent --new-session --unshare-all \
    --ro-bind /usr /usr \
    --symlink usr/bin /bin --symlink usr/lib /lib --symlink usr/sbin /sbin \
    --proc /proc --dev /dev --tmpfs /tmp \
    --dir /home/remy \
    --bind  "$SKILL_DIR"  /home/remy/skill \
    --ro-bind "$SKILL_VENV" /home/remy/venv \
    --clearenv --setenv HOME /home/remy \
    --setenv PATH /home/remy/venv/bin:/usr/bin:/bin \
    --chdir /home/remy/skill \
    /home/remy/venv/bin/python3 handler.py
```

Notes: root is tmpfs, so `~/.remy`, secrets, and the REMY repo simply do not
exist inside. Network variant: replace `--unshare-all` with
`--unshare-user --unshare-pid --unshare-ipc --unshare-uts --unshare-cgroup`
(keeps host net) and add `--ro-bind /etc/resolv.conf /etc/resolv.conf
--ro-bind /etc/ssl /etc/ssl --ro-bind /etc/ca-certificates /etc/ca-certificates`.
Domain-level filtering is NOT possible with bwrap alone; that needs the srt
proxy pattern (see anthropic-experimental-sandbox-runtime dive).

Profile B, pip install into a dedicated venv (network to PyPI, write only the
venv):

```
systemd-run --user --scope --collect -q \
  -p MemoryMax=1G -p TasksMax=128 -p RuntimeMaxSec=600 \
  bwrap \
    --die-with-parent --new-session \
    --unshare-user --unshare-pid --unshare-ipc --unshare-uts --unshare-cgroup \
    --ro-bind /usr /usr \
    --symlink usr/bin /bin --symlink usr/lib /lib --symlink usr/sbin /sbin \
    --ro-bind /etc /etc \
    --proc /proc --dev /dev --tmpfs /tmp \
    --dir /home/remy \
    --bind "$VENV" /home/remy/venv \
    --clearenv --setenv HOME /home/remy \
    --setenv PATH /home/remy/venv/bin:/usr/bin:/bin \
    --setenv PIP_CACHE_DIR /tmp/pip-cache \
    /home/remy/venv/bin/pip install --no-input -r /home/remy/venv/requirements.txt
```

Notes: `--ro-bind /etc /etc` is coarse but /etc holds no REMY secrets; pip
cache goes to the private tmpfs (trade: no cross-install cache; bind a
persistent `--bind $CACHE /home/remy/.cache/pip` if wheel rebuild time on
Orin hurts).

Profile C, full toolchain job (project workdir writable, net, git+compilers,
no ~/.remy, no REMY repo):

```
systemd-run --user --scope --collect -q \
  -p MemoryMax=3G -p TasksMax=1024 -p RuntimeMaxSec=7200 \
  bwrap \
    --die-with-parent --new-session \
    --unshare-user --unshare-pid --unshare-ipc --unshare-uts --unshare-cgroup \
    --ro-bind /usr /usr \
    --symlink usr/bin /bin --symlink usr/lib /lib --symlink usr/sbin /sbin \
    --ro-bind /etc /etc --ro-bind /opt /opt \
    --proc /proc --dev /dev --tmpfs /tmp \
    --dir /home/remy \
    --bind "$JOB_WORKDIR" /home/remy/work \
    --ro-bind "$HOME/.gitconfig" /home/remy/.gitconfig \
    --ro-bind "$HOME/.cache/pip" /home/remy/.cache/pip \
    --clearenv --setenv HOME /home/remy --setenv USER remy \
    --setenv PATH /usr/local/bin:/usr/bin:/bin \
    --chdir /home/remy/work \
    bash -lc "$JOB_CMD"
```

Notes: `claude -p` itself can run inside this (node lives in /usr or bind the
nvm dir ro); pass the API/OAuth credential via `--setenv` explicitly, never by
binding `~/.claude`. CUDA jobs additionally need `--ro-bind /usr/local/cuda
/usr/local/cuda --dev-bind /dev/nvhost* ...` (enumerate on-box; `--dev /dev`
gives only the standard nodes).

## Gotchas (verify on-box)
- `CONFIG_USER_NS=y` and unprivileged userns creation: Ubuntu 22.04 userspace
  does not restrict it (the apparmor userns clamp arrived in 23.10/24.04), but
  L4T r36 uses NVIDIA's kernel config. Check: `unshare -Ur true` as remy.
  Historical L4T releases shipped without userns (NVIDIA forum thread
  "Enable CONFIG_NAMESPACES and CONFIG_USER_NS in final L4T 32.X"); r36 is
  expected OK but must be proven before this whole plan stands.
- No setuid fallback: jammy's bwrap is non-setuid; if userns is off the only
  fix is a kernel rebuild, not a bwrap flag.
- 0.6.1 flag set: no `--disable-userns`, no `--overlay`. Everything used above
  exists in 0.6.1.
- `--dev /dev` hides GPU nodes; profile A/B correctly get no GPU.
- Overhead per invocation: fork + mount-ns assembly, ~10-30ms on Orin-class
  CPU (**ESTIMATE**); python interpreter start inside dominates (~200-500ms,
  **ESTIMATE**).

## Avoid
Statically linking the LGPL C; hand-rolling per-skill ad-hoc flags at call
sites (centralize the three profiles in one module, e.g.
`remy/sandbox/profiles.py`).

## License constraint
LGPL-2.0-or-later; exec as separate process is fine (DEPEND, process
boundary).

## Effort
**M** — three fixed profiles + a small argv builder + on-box userns check in
selftest.
