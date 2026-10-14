"""
Data models and the exception hierarchy shared across the whole server.

Every service function either returns an ``OperationResult`` (success) or
raises a subclass of :class:`WorkspaceError` (failure). The MCP tool layer
never lets a raw exception escape to the client -- it always catches
``WorkspaceError`` and converts it into a structured, informative payload.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------- #
# Exceptions
# --------------------------------------------------------------------------- #


class WorkspaceError(Exception):
    """Base class for every error the server raises intentionally.

    Attributes:
        message: Human-readable explanation, safe to show to the end user.
        code: A short machine-readable identifier (e.g. ``"PATH_TRAVERSAL"``).
        details: Optional extra structured context (e.g. offending path).
    """

    code: str = "WORKSPACE_ERROR"

    def __init__(self, message: str, **details: Any) -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def to_dict(self) -> dict[str, Any]:
        return {"error_code": self.code, "message": self.message, **self.details}


class PathTraversalError(WorkspaceError):
    code = "PATH_TRAVERSAL"


class WorkspaceViolationError(WorkspaceError):
    code = "WORKSPACE_VIOLATION"


class SymlinkEscapeError(WorkspaceError):
    code = "SYMLINK_ESCAPE"


class InvalidPathError(WorkspaceError):
    code = "INVALID_PATH"


class NotFoundError(WorkspaceError):
    code = "NOT_FOUND"


class AlreadyExistsError(WorkspaceError):
    code = "ALREADY_EXISTS"


class DuplicateFileError(WorkspaceError):
    code = "DUPLICATE_FILE"


class PermissionDeniedError(WorkspaceError):
    code = "PERMISSION_DENIED"


class FileTooLargeError(WorkspaceError):
    code = "FILE_TOO_LARGE"


class UnsupportedExtensionError(WorkspaceError):
    code = "UNSUPPORTED_EXTENSION"


class ConfirmationRequiredError(WorkspaceError):
    code = "CONFIRMATION_REQUIRED"


class ProtectedFileError(WorkspaceError):
    code = "PROTECTED_FILE"


# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #


class OperationStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"


class EntryType(str, Enum):
    FILE = "file"
    DIRECTORY = "directory"
    SYMLINK = "symlink"
    OTHER = "other"


# --------------------------------------------------------------------------- #
# Result / info models
# --------------------------------------------------------------------------- #


class OperationResult(BaseModel):
    """The uniform envelope returned by every MCP tool."""

    status: OperationStatus
    operation: str
    target_path: str = ""
    message: str = ""
    duration_ms: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    data: Optional[dict[str, Any]] = None
    error_code: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:  # pydantic v2 hook
        # Keep timestamps deterministic in format: ISO-8601 with 'Z'.
        pass


class Timer:
    """Small context-manager-free helper to measure wall-clock duration."""

    def __init__(self) -> None:
        self._start = time.perf_counter()

    def elapsed_ms(self) -> float:
        return round((time.perf_counter() - self._start) * 1000, 3)


class DirectoryEntryInfo(BaseModel):
    name: str
    path: str
    type: EntryType
    size_bytes: Optional[int] = None
    modified: Optional[str] = None
    extension: Optional[str] = None


class FileInfo(BaseModel):
    path: str
    size_bytes: int
    modified: str
    created: str
    extension: str
    line_count: Optional[int] = None


class ProjectInfo(BaseModel):
    name: str
    path: str
    created: str
    structure: list[str]


class SearchMatch(BaseModel):
    path: str
    line_number: int
    line_text: str


class CloudLogEntry(BaseModel):
    """A single line item recorded for the CLOUD.md AI work log."""

    category: str  # e.g. "Files Created", "Architecture Decisions"
    description: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
