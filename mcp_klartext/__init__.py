"""MCP server for brand-aware copywriting."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("mcp-klartext")
except PackageNotFoundError:
    __version__ = "unknown"
