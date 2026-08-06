# google/nsjail — IGNORE (bwrap + systemd scope covers it; build friction on arm64)

Google's process jail: namespaces + Kafel seccomp-bpf policies + rlimits +
cgroup limits, configured by flags or a protobuf config file. Technically the
most complete single-tool answer to profiles A/B/C, and it builds on arm64,
but it is not packaged in Ubuntu jammy, needs protobuf/libnl build deps, and
everything REMY needs from it is already covered by apt-installable bwrap
(namespaces) plus a systemd-run scope (limits).

- **Stars/health:** 4.0k, active (2026-07) · **License:** Apache-2.0

## Does better than REMY
Declarative per-jail policy files (one .cfg per containment profile, reviewed
in git) and integrated resource limits, which bwrap lacks:

## Read these files
- `google/nsjail@5ebcc30:README.md:L11-26` — Kafel seccomp policies, protobuf
  config files, and the build-from-source dep list (autoconf, bison, flex,
  libprotobuf-dev, libnl-route-3-dev, protobuf-compiler): the arm64 story is
  "compile it yourself".
- `google/nsjail@5ebcc30:README.md:L91-93` and `L294-296` — `--rlimit_as/
  --rlimit_cpu/--rlimit_nofile` and `--cgroup_mem_max/--cgroup_pids_max/
  --cgroup_cpu_ms_per_sec`: the exact limit vocabulary REMY's profiles need
  (delivered instead via systemd `MemoryMax=/TasksMax=/RuntimeMaxSec=`).

## Lift
Only the idea: keep each containment profile as a declarative, version-
controlled document (REMY: a frozen dataclass per profile), not string-built
argv scattered through call sites.

## Avoid
Adopting it: unpackaged binary REMY must build and update itself, on the
device, for marginal gain over bwrap; Kafel syscall policies are overkill for
v1 and easy to get wrong (breakage presents as flaky skills).

## License constraint
Apache-2.0 (moot; not adopted).

## Effort
n/a (pattern noted in bubblewrap dive).
