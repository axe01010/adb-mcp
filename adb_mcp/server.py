"""adb-mcp server — expose adb as MCP tools to any AI agent."""

from __future__ import annotations

import logging
from typing import Optional

from fastmcp import FastMCP

from .adb import Adb, MockAdb

log = logging.getLogger("adb-mcp")


def build_server(device: Optional[str] = None, mock: bool = False) -> FastMCP:
    adb: Adb = MockAdb(device=device) if mock else Adb(device=device)
    mcp = FastMCP("adb-mcp")

    @mcp.tool()
    def list_devices() -> list[str]:
        """List connected Android devices over adb."""
        return adb.devices()

    @mcp.tool()
    def screencap(device: str = "") -> str:
        """Capture the screen; returns a PNG filename on the device's /sdcard."""
        out = adb.raw("exec-out", "screencap", "-p")
        return f"captured {len(out)} bytes of PNG" if out else "no capture"

    @mcp.tool()
    def tap(x: int, y: int) -> str:
        """Tap at screen coordinate (x, y)."""
        return adb.shell(f"input tap {x} {y}") or f"tapped {(x, y)}"

    @mcp.tool()
    def swipe(x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> str:
        """Swipe from (x1,y1) to (x2,y2) over duration_ms."""
        return adb.shell(f"input swipe {x1} {y1} {x2} {y2} {duration_ms}") or "swiped"

    @mcp.tool()
    def input_text(text: str) -> str:
        """Type text into the focused field."""
        return adb.shell(f"input text {text!r}") or "typed"

    @mcp.tool()
    def keyevent(keycode: int) -> str:
        """Send a key event, e.g. 3 (home), 4 (back), 187 (app apps)."""
        return adb.shell(f"input keyevent {keycode}") or f"sent keyevent {keycode}"

    @mcp.tool()
    def list_packages() -> list[str]:
        """List installed packages starting with the given prefix (default all)."""
        out = adb.shell("pm list packages")
        return [ln.replace("package:", "") for ln in out.splitlines() if ln.strip()]

    @mcp.tool()
    def install_apk(local: str) -> str:
        """Install an APK on the device."""
        return adb.raw("install", "-r", local).strip() or "installed"

    @mcp.tool()
    def logcat(lines: int = 50) -> str:
        """Dump the last `lines` of the device logcat buffer."""
        return adb.shell(f"logcat -d -t {lines}")

    @mcp.tool()
    def battery() -> str:
        """Return battery status snapshot."""
        return adb.shell("dumpsys battery") or "unknown"

    @mcp.tool()
    def launch(package: str, activity: str = "") -> str:
        """Launch an app; optionally a specific activity."""
        target = package if not activity else f"{package}/{activity}"
        return adb.shell(f"am start -n {target}") or f"launched {package}"

    return mcp


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(prog="adb-mcp", description="Expose adb as MCP tools.")
    ap.add_argument("--device", default=None, help="target adb serial")
    ap.add_argument("--mock", action="store_true", help="run against a mock adb (no device)")
    ap.add_argument("--transport", default="stdio", choices=["stdio", "sse"])
    args = ap.parse_args()

    server = build_server(device=args.device, mock=args.mock)
    log.info("adb-mcp starting (mock=%s) over %s", args.mock, args.transport)
    server.run(transport=args.transport)


if __name__ == "__main__":
    main()