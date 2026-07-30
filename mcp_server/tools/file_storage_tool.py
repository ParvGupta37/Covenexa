"""
File Storage MCP Tool.
Agents use this tool to read and list uploaded files.
They must NEVER access the filesystem directly.
"""
import logging
import os
from pathlib import Path
from typing import Any

import aiofiles

from mcp_server.tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


class FileStorageTool(BaseTool):
    """
    MCP Tool: Read/list files from the uploads directory.

    Supported operations:
      - read_file: Read binary or text content of an uploaded file
      - list_files: List files in the uploads directory (optionally filtered)
      - file_exists: Check if a file exists
      - get_metadata: Return file size, extension, and creation time
    """

    def __init__(self, base_upload_dir: str = "/app/uploads") -> None:
        self._base_dir = Path(base_upload_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    @property
    def name(self) -> str:
        return "file_storage"

    @property
    def description(self) -> str:
        return (
            "Read and list uploaded files from the Covenexa file storage. "
            "Use 'read_file' to get file content for parsing. "
            "Use 'list_files' to enumerate available documents. "
            "All paths are relative to the uploads directory."
        )

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        operation = kwargs.get("operation", "list_files")

        try:
            if operation == "read_file":
                return await self._read_file(
                    kwargs.get("file_path", ""),
                    kwargs.get("mode", "rb"),
                )
            elif operation == "list_files":
                return await self._list_files(
                    kwargs.get("subdirectory", ""),
                    kwargs.get("extension_filter"),
                )
            elif operation == "file_exists":
                return await self._file_exists(kwargs.get("file_path", ""))
            elif operation == "get_metadata":
                return await self._get_metadata(kwargs.get("file_path", ""))
            else:
                return {"success": False, "data": None, "error": f"Unknown operation: {operation}"}
        except Exception as exc:
            logger.error("FileStorageTool error [op=%s]: %s", operation, exc)
            return {"success": False, "data": None, "error": str(exc)}

    def _resolve_path(self, file_path: str) -> Path:
        """
        Safely resolve a relative file path within the uploads directory.
        Prevents path traversal attacks.
        """
        resolved = (self._base_dir / file_path).resolve()
        if not str(resolved).startswith(str(self._base_dir.resolve())):
            raise PermissionError(f"Access denied: path traversal detected for '{file_path}'")
        return resolved

    async def _read_file(
        self,
        file_path: str,
        mode: str = "rb",
    ) -> dict[str, Any]:
        """Read file content. Returns base64-encoded bytes for binary files."""
        path = self._resolve_path(file_path)
        if not path.exists():
            return {"success": False, "data": None, "error": f"File not found: {file_path}"}

        async with aiofiles.open(path, mode=mode) as f:
            content = await f.read()

        if mode == "rb":
            import base64
            encoded = base64.b64encode(content).decode("utf-8")
            return {
                "success": True,
                "data": {
                    "file_path": file_path,
                    "content_base64": encoded,
                    "size_bytes": len(content),
                },
                "error": None,
            }
        return {
            "success": True,
            "data": {"file_path": file_path, "content": content, "size_bytes": len(content)},
            "error": None,
        }

    async def _list_files(
        self,
        subdirectory: str = "",
        extension_filter: str | None = None,
    ) -> dict[str, Any]:
        """List files, optionally filtered by extension (e.g. 'pdf')."""
        target = self._resolve_path(subdirectory) if subdirectory else self._base_dir
        if not target.exists():
            return {"success": True, "data": {"files": []}, "error": None}

        files = []
        for entry in target.iterdir():
            if entry.is_file():
                if extension_filter and entry.suffix.lstrip(".") != extension_filter:
                    continue
                files.append({
                    "name": entry.name,
                    "path": str(entry.relative_to(self._base_dir)),
                    "size_bytes": entry.stat().st_size,
                    "extension": entry.suffix.lstrip("."),
                })
        return {"success": True, "data": {"files": files}, "error": None}

    async def _file_exists(self, file_path: str) -> dict[str, Any]:
        path = self._resolve_path(file_path)
        return {"success": True, "data": {"exists": path.exists()}, "error": None}

    async def _get_metadata(self, file_path: str) -> dict[str, Any]:
        path = self._resolve_path(file_path)
        if not path.exists():
            return {"success": False, "data": None, "error": f"File not found: {file_path}"}
        stat = path.stat()
        return {
            "success": True,
            "data": {
                "name": path.name,
                "extension": path.suffix.lstrip("."),
                "size_bytes": stat.st_size,
                "created_at": stat.st_ctime,
                "modified_at": stat.st_mtime,
            },
            "error": None,
        }
