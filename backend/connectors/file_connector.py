"""File Connector for controlled local file system access."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.connectors.base import Connector, Resource
from backend.core.config import UPLOADS_DIR


class FileConnector(Connector):
    """Provides restricted read/write access to the uploads directory."""

    def __init__(self, allowed_directory: str | Path | None = None):
        raw_path = allowed_directory if allowed_directory is not None else UPLOADS_DIR
        self.allowed_directory = Path(raw_path).resolve()
        self.allowed_directory.mkdir(parents=True, exist_ok=True)

    def get_name(self) -> str:
        return "LocalFileConnector"

    def _is_safe_path(self, file_path: str) -> Path:
        """Validate that the requested path is inside the allowed directory."""
        clean_path = file_path.lstrip("/").lstrip("\\")
        requested_path = (self.allowed_directory / clean_path).resolve()

        try:
            requested_path.relative_to(self.allowed_directory)
        except ValueError:
            raise PermissionError(
                f"Access denied: path '{file_path}' is outside the allowed directory."
            )

        return requested_path

    async def list_resources(self) -> List[Resource]:
        """List all files in the allowed directory."""
        resources = []
        for file in sorted(self.allowed_directory.iterdir()):
            if file.is_file() and file.name != ".gitkeep":
                resources.append(
                    Resource(
                        id=file.name,
                        name=file.name,
                        description=f"Uploaded file: {file.name}",
                        type="file",
                    )
                )
        return resources

    async def read(self, resource_id: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Read text content from a file (supports .txt, .pdf, .docx)."""
        safe_path = self._is_safe_path(resource_id)

        if not safe_path.exists():
            raise FileNotFoundError(f"File '{resource_id}' not found.")

        suffix = safe_path.suffix.lower()
        if suffix == ".pdf":
            from backend.services.resume_ingestion import extract_text
            return extract_text(safe_path.read_bytes(), "application/pdf")
        if suffix == ".docx":
            from backend.services.resume_ingestion import extract_text
            return extract_text(
                safe_path.read_bytes(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

        with open(safe_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    async def write(self, resource_id: str, data: Any) -> dict:
        """Write text data to a file."""
        safe_path = self._is_safe_path(resource_id)
        safe_path.parent.mkdir(parents=True, exist_ok=True)

        content = str(data)
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(content)

        return {"status": "success", "file": resource_id, "bytes_written": len(content)}

    async def execute(self, action: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a file-related action (delete, stat, parse_resume)."""
        params = params or {}
        resource_id = params.get("resource_id")

        if not resource_id:
            raise ValueError("execute requires a 'resource_id' parameter.")

        safe_path = self._is_safe_path(resource_id)

        if action == "delete":
            if safe_path.exists():
                safe_path.unlink()
                return {"status": "deleted", "file": resource_id}
            raise FileNotFoundError(f"File '{resource_id}' not found.")
        elif action == "stat":
            if safe_path.exists():
                stat = safe_path.stat()
                return {"size": stat.st_size, "modified": stat.st_mtime}
            raise FileNotFoundError(f"File '{resource_id}' not found.")
        elif action == "parse_resume":
            if not safe_path.exists():
                raise FileNotFoundError(f"File '{resource_id}' not found.")
            from backend.services.resume_ingestion import parse_profile
            text = await self.read(resource_id)
            return dict(parse_profile(text, file_name=safe_path.name))
        else:
            raise NotImplementedError(f"Action '{action}' is not supported by FileConnector.")