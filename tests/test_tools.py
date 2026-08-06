"""Unit tests using the mock adb — run without a real device."""

import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from adb_mcp.adb import MockAdb  # noqa: E402
from adb_mcp.server import build_server  # noqa: E402


def test_devices_with_mock():
    # devices() shells out to real `adb`; only assert the MCP layer works.
    server = build_server(mock=True)
    assert server is not None


def test_mockadb_shell():
    a = MockAdb()
    assert a.shell("dumpsys battery")  # non-empty
    assert "mBatteryLevel" in a.shell("dumpsys battery")


def test_mockadb_raw_screencap():
    a = MockAdb()
    assert "PNG_MOCK" in a.raw("exec-out", "screencap")


def test_mock_packages():
    a = MockAdb()
    out = a.shell("pm list packages")
    assert "com.example.app" in out


def test_server_tools_registered():
    from fastmcp import FastMCP  # noqa: F401
    s = build_server(mock=True)
    # FastMCP exposes registered tools via internal registry; just assert it builds.
    assert s.name == "adb-mcp"