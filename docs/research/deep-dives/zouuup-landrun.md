# Zouuup/landrun — DEPEND (conditional: only if L4T kernel enables Landlock)

Single static Go binary that sandboxes a command with kernel Landlock rules:
`landrun --rox /usr --rw $DIR cmd`. No namespaces, no root, no setuid, no
daemon; the kernel LSM enforces path rules even after fork/exec. The natural
lighter-weight alternative (or additive second layer) to bwrap, with one fatal
dependency: the kernel must be built with `CONFIG_SECURITY_LANDLOCK=y` AND
have `landlock` in the boot-time `lsm=` list, which NVIDIA's L4T config is not
known to do.

- **Stars/health:** 2.3k, active (2026-07) · **License:** MIT

## Does better than REMY
Kernel-enforced fs policy with zero infrastructure. Unlike bwrap it does not
need user namespaces at all, so it survives a Jetson kernel that lacks
CONFIG_USER_NS. Composable: Landlock rules stack, so REMY could apply a broad
Landlock policy AND bwrap.

## Read these files
- `Zouuup/landrun@811cfff:README.md:L31-37` — requirements: kernel 5.13+ for
  fs rules; kernel 6.7+ (ABI v4) for TCP bind/connect rules. Jetson's 5.15 =
  ABI v1 at best: FS ONLY, no network restriction, no truncate right. Use
  `--best-effort` so it degrades instead of failing.
- `Zouuup/landrun@811cfff:README.md:L92-122` — full flag surface: `--rox/--ro/
  --rw/--rwx`, `--env` (env is stripped by default), `--add-exec`, `--ldd`,
  and the ABI v6+/v9+ IPC and unix-socket scoping REMY will not get on 5.15.

## Lift
Profile A/B on a userns-less kernel: `landrun --best-effort --rox /usr --ro
/etc --rwx $SKILL_DIR --rw /tmp --env PATH python3 handler.py`. Remember on
5.15 this constrains the filesystem ONLY: network stays open, no memory/CPU
caps (still wrap in systemd-run scope), /proc still visible.

## Avoid
Treating it as the primary sandbox on this box: 5.15 Landlock cannot block
network, signals, or unix sockets, so a hostile skill can still talk to
REMY's local sockets. On-box gate first: `grep -q landlock
/sys/kernel/security/lsm` (expected absent on stock L4T; if absent, IGNORE
until a kernel rebuild).

## License constraint
MIT. Could even be vendored, but a `go build` dep is simpler.

## Effort
**S** — single binary + one profile function; the cost is the kernel verify.
