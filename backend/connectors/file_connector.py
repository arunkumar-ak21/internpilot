"""File Connector for controlled local file system access."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.connectors.base import Connector, Resource
from backend.core.config import get_settings


class FileConnector(Connector):
    """Provides restricted read/write access to the uploads directory."""

    def __init__(self, allowed_directory: str | Path | None = None):
        settings = get_settings()
        # Resolve to absolute path to prevent traversal tricks
        raw_path = allowed_directory or settings.UPLOADS_DIR
        self.allowed_directory = Path(raw_path).resolve()
        
        # Ensure the directory exists
        self.allowed_directory.mkdir(parents=True, exist_ok=True)

    def get_name(self) -> str:
        return "LocalFileConnector"

    def _is_safe_path(self, file_path: str) -> Path:
        """Validate that the requested path is inside the allowed directory."""
        # Strip leading slashes to prevent absolute path injection via joining
        clean_path = file_path.lstrip("/")
        clean_path = clean_path.lstrip("\\")
        
        requested_path = (self.allowed_directory / clean_path).resolve()
        
        try:
            # Check if the requested path is relative to the allowed directory
            requested_path.relative_to(self.allowed_directory)
        except ValueError:
            raise PermissionError(f"Access denied: path '{file_path}' is outside the allowed directory.")
            
        return requested_path

    async def list_resources(self) -> List[Resource]:
        """List all files in the allowed directory."""
        resources = []
        for file in self.allowed_directory.iterdir():
            if file.is_file():
                resources.append(
                    Resource(
                        id=file.name,
                        name=file.name,
                        description=f"File: {file.name}",
                        type="file"
                    )
                )
        return resources

    async def read(self, resource_id: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Read text content from a file."""
        safe_path = self._is_safe_path(resource_id)
        
        if not safe_path.exists():
            raise FileNotFoundError(f"File '{resource_id}' not found.")
            
        with open(safe_path, "r", encoding="utf-8") as f:
            return f.read()

    async def write(self, resource_id: str, data: Any) -> dict:
        """Write text data to a file."""
        safe_path = self._is_safe_path(resource_id)
        
        # Ensure parent directories exist
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        
        content = str(data)
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return {"status": "success", "file": resource_id, "bytes_written": len(content)}

    async def execute(self, action: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a file-related action (e.g., delete, stat)."""
        params = params or {}
        resource_id = params.get("resource_id")
        
        if not resource_id:
            raise ValueError("execute requires a 'resource_id' parameter.")
            
        safe_path = self._is_safe_path(resource_id)
        
        if action == "delete":
            if safe_path.exists():
                safe_path.unlink()
                return {"status": "deleted", "file": resource_id}
            else:
                raise FileNotFoundError(f"File '{resource_id}' not found.")
        elif action == "stat":
            if safe_path.exists():
                stat = safe_path.stat()
                return {"size": stat.st_size, "modified": stat.st_mtime}
            else:
                raise FileNotFoundError(f"File '{resource_id}' not found.")
        else:
            raise NotImplementedError(f"Action '{action}' is not supported by FileConnector.")
