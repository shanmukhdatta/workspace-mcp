"""Versioned, opt-in restoration of pre-mutation file snapshots.

Snapshots live outside the projects in the protected .workspace_mcp directory.
Only previously validated workspace files may be snapshotted/restored.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from workspace_mcp.config.settings import WorkspaceSettings
from workspace_mcp.models.schemas import ConfirmationRequiredError, NotFoundError, WorkspaceError
from workspace_mcp.utils.pathsec import PathValidator


class BackupService:
    def __init__(self, settings: WorkspaceSettings, validator: PathValidator) -> None:
        self.settings = settings
        self.validator = validator
        self.root = settings.resolved_backup_dir()

    def snapshot(self, path: Path) -> str | None:
        """Create a verifiable backup before overwriting or deleting a file."""
        rel = path.relative_to(self.validator.workspace_root)
        self.validator.assert_not_protected(path)
        if not path.is_file() or path.is_symlink():
            return None
        if path.stat().st_size > self.settings.max_backup_file_size_bytes:
            raise WorkspaceError(
                "File exceeds backup size limit; mutation cancelled.", path=str(rel)
            )
        backup_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex
        dest = self.root / backup_id
        dest.mkdir(parents=True, exist_ok=False)
        snapshot = dest / "content"
        try:
            shutil.copy2(path, snapshot)
            data = snapshot.read_bytes()
            manifest = {
                "path": rel.as_posix(),
                "sha256": hashlib.sha256(data).hexdigest(),
                "size": len(data),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            (dest / "metadata.json").write_text(json.dumps(manifest), encoding="utf-8")
        except Exception:
            shutil.rmtree(dest)
            raise
        return backup_id

    def list_backups(self, path: str = "") -> list[dict]:
        if path:
            expected = self.validator.relative_to_root(self.validator.resolve(path))
        else:
            expected = ""
        result = []
        for folder in sorted(self.root.iterdir(), reverse=True):
            if not re.fullmatch(r"\d{8}T\d{6}-[0-9a-f]{32}", folder.name):
                continue
            try:
                data = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
                if not expected or data["path"] == expected:
                    result.append({"backup_id": folder.name, **data})
            except (OSError, KeyError, ValueError, TypeError):
                continue
        result.sort(key=lambda row: row["created_at"], reverse=True)
        return result

    def restore(self, backup_id: str, *, confirm: bool = False) -> str:
        if not confirm:
            raise ConfirmationRequiredError("Restoration requires confirm=True.")
        if not re.fullmatch(r"\d{8}T\d{6}-[0-9a-f]{32}", backup_id):
            raise NotFoundError("Invalid backup identifier.")
        folder = self.root / backup_id
        try:
            metadata = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
            content = (folder / "content").read_bytes()
        except (OSError, ValueError, TypeError) as exc:
            raise NotFoundError("Backup not found.", backup_id=backup_id) from exc
        if hashlib.sha256(content).hexdigest() != metadata.get("sha256"):
            raise WorkspaceError("Backup checksum failed; restore cancelled.")
        target = self.validator.resolve(metadata["path"])
        self.validator.assert_not_protected(target)
        if target.is_symlink() or target.is_dir():
            raise WorkspaceError("Cannot restore onto a symlink or directory.")
        if len(content) > self.settings.max_file_size_bytes:
            raise WorkspaceError("Backup exceeds current file size limit.")
        if target.is_file():
            self.snapshot(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(target.name + ".restoring-" + uuid.uuid4().hex)
        try:
            tmp.write_bytes(content)
            tmp.replace(target)
        finally:
            tmp.unlink(missing_ok=True)
        return self.validator.relative_to_root(target)
