"""Age-encrypted secret store (ADR 0004).

One encrypted file per credential under ~/.remy/secrets/ (0700, outside the git
tree), decryptable only by the broker via an age X25519 identity file (0600).
The crypto backend is injected so the store's file/permission logic is testable
without the `age` binary; the real AgeBackend shells out to age (exec boundary,
so age's license never links into REMY).
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Protocol


class CryptoBackend(Protocol):
    def encrypt(self, plaintext: bytes) -> bytes: ...
    def decrypt(self, ciphertext: bytes) -> bytes: ...


class AgeBackend:
    """Encrypt/decrypt by shelling out to the `age` binary."""

    def __init__(self, recipient: str, identity_file: str | Path,
                 binary: str = "age") -> None:
        self.recipient = recipient
        self.identity_file = Path(identity_file).expanduser()
        self.binary = binary

    def encrypt_argv(self) -> list[str]:
        # read plaintext on stdin, write binary ciphertext to stdout
        return [self.binary, "-r", self.recipient, "-o", "-"]

    def decrypt_argv(self) -> list[str]:
        return [self.binary, "-d", "-i", str(self.identity_file)]

    def encrypt(self, plaintext: bytes) -> bytes:
        return self._run(self.encrypt_argv(), plaintext, "encrypt")

    def decrypt(self, ciphertext: bytes) -> bytes:
        return self._run(self.decrypt_argv(), ciphertext, "decrypt")

    @staticmethod
    def _run(argv: list[str], data: bytes, op: str) -> bytes:
        # `from None` drops the CalledProcessError, whose .stderr/.stdout could
        # carry plaintext or key material, out of the traceback chain.
        try:
            return subprocess.run(argv, input=data, capture_output=True,
                                  check=True).stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"age {op} failed (exit {e.returncode})") from None


class SecretStore:
    def __init__(self, directory: str | Path, backend: CryptoBackend) -> None:
        self.dir = Path(directory).expanduser()
        self._backend = backend

    def _path(self, name: str) -> Path:
        if (not name or "/" in name or "\\" in name or name.startswith(".")
                or "\x00" in name):
            raise ValueError(f"bad credential name: {name!r}")
        path = self.dir / f"{name}.age"
        # Defense in depth: the resolved path must stay inside the store.
        if not path.resolve().is_relative_to(self.dir.resolve()):
            raise ValueError(f"credential name escapes store: {name!r}")
        return path

    def ensure_dir(self) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        try:
            self.dir.chmod(0o700)
        except OSError:
            pass

    def put(self, name: str, value: str) -> None:
        self.ensure_dir()
        path = self._path(name)
        data = self._backend.encrypt(value.encode("utf-8"))
        # Create 0600 from the start (no world-readable window), and chmod after
        # in case the file already existed with looser perms.
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        try:
            path.chmod(0o600)
        except OSError:
            pass

    def get(self, name: str) -> str | None:
        path = self._path(name)
        if not path.is_file():
            return None
        return self._backend.decrypt(path.read_bytes()).decode("utf-8")

    def names(self) -> list[str]:
        if not self.dir.is_dir():
            return []
        return sorted(p.stem for p in self.dir.glob("*.age"))

    def delete(self, name: str) -> bool:
        path = self._path(name)
        if path.is_file():
            path.unlink()
            return True
        return False
