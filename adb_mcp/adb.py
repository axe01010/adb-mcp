"""ADB transport — thin, shellable wrapper around `adb` with an optional mock."""

from __future__ import annotations

import shlex
import subprocess
from typing import Optional


class Adb:
    """Runs `adb` commands. Use `MockAdb` (or the `--mock` flag) to test offline."""

    def __init__(self, device: Optional[str] = None, adb_path: str = "adb"):
        self.device = device
        self.adb_path = adb_path

    def _base(self) -> list[str]:
        return [self.adb_path] + (["-s", self.device] if self.device else [])

    def shell(self, cmd: str) -> str:
        """Run `adb shell <cmd>` and return trimmed stdout (stderr swallowed)."""
        out = subprocess.run(
            self._base() + ["shell"] + shlex.split(cmd),
            capture_output=True, text=True, timeout=60,
        )
        return out.stdout.strip()

    def raw(self, *args: str) -> str:
        """Run an arbitrary adb subcommand, e.g. raw('screencap', '-p')."""
        out = subprocess.run(
            self._base() + list(args), capture_output=True, text=True, timeout=120,
        )
        return out.stdout

    def devices(self) -> list[str]:
        out = subprocess.run([self.adb_path, "devices"], capture_output=True, text=True)
        lines = [ln.split("\t")[0] for ln in out.stdout.strip().splitlines()[1:] if "device" in ln]
        return lines


class MockAdb(Adb):
    """In-memory stand-in for CI/tests — no real device needed."""

    def __init__(self, device: Optional[str] = None):
        super().__init__(device=device, adb_path="adb")

    def shell(self, cmd: str) -> str:
        c = cmd.strip().split()[0] if cmd.strip() else ""
        fake = {
            "settings": "max_brightness=2047",
            "getevent": "",
            "ls": "test.apk\napp.txt",
            "pm": "package:com.example.app\npackage:com.android.settings\npackage:org.termux",
            "input": "",
            "dumpsys": "mBatteryLevel: 81",
        }
        return fake.get(c, "")

    def raw(self, *args: str) -> str:
        if "screencap" in args:
            return "PNG_MOCK"
        if "list" in args and "packages" in " ".join(args):
            return "package:com.example.app\npackage:com.android.settings"
        return ""