"""Incremental code-chunk index with lexical fallback and optional local embeddings.

The lexical mode is not claimed to be semantic search. To enable genuine semantic
retrieval supply a local SentenceTransformer model path and install the optional
embedding extra. The library never downloads a model by itself.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
from pathlib import Path

from workspace_mcp.config.settings import WorkspaceSettings
from workspace_mcp.models.schemas import WorkspaceError
from workspace_mcp.utils.pathsec import PathValidator

TOKEN = re.compile(r"[A-Za-z_][A-Za-z_0-9]{1,}")
EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".rs",
    ".go",
    ".md",
    ".java",
    ".c",
    ".cpp",
    ".json",
}


class IndexService:
    def __init__(self, settings: WorkspaceSettings, validator: PathValidator) -> None:
        self.settings = settings
        self.validator = validator
        self.db = settings.resolved_index_dir() / "code_index.sqlite3"
        self._embedder = None

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.db, timeout=15)
        db.execute("""CREATE TABLE IF NOT EXISTS chunks (
            project TEXT NOT NULL, path TEXT NOT NULL, part INTEGER NOT NULL,
            filehash TEXT NOT NULL, body TEXT NOT NULL, vector TEXT,
            PRIMARY KEY(project, path, part))""")
        db.execute("CREATE INDEX IF NOT EXISTS idx_chunks_project ON chunks(project)")
        return db

    def _model(self):
        if not self.settings.semantic_model_path:
            return None
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise WorkspaceError(
                    "Install sentence-transformers into this environment to enable local semantic search."
                ) from exc
            # A locally available model is required; no implicit internet downloads.
            model = Path(self.settings.semantic_model_path)
            if not model.is_dir():
                raise WorkspaceError("semantic_model_path must be a local directory.")
            self._embedder = SentenceTransformer(str(model), local_files_only=True)
        return self._embedder

    def _root(self, project: str) -> Path:
        root = self.validator.resolve(project)
        if root.parent != self.validator.workspace_root or not root.is_dir():
            raise WorkspaceError("Index an existing top-level workspace project.")
        return root

    def index(self, project: str, max_files: int = 5000) -> dict:
        root = self._root(project)
        if not 1 <= max_files <= 100000:
            raise WorkspaceError("max_files must be between 1 and 100000.")
        model = self._model()
        visited: set[str] = set()
        updated = 0
        skipped = 0
        with self._connect() as db:
            previous = dict(
                db.execute(
                    "SELECT path, MAX(filehash) FROM chunks WHERE project=? GROUP BY path",
                    (project,),
                ).fetchall()
            )
            for path in root.rglob("*"):
                if len(visited) >= max_files:
                    break
                if any(
                    part in self.settings.ignored_dirs or part == ".workspace_mcp"
                    for part in path.relative_to(root).parts
                ):
                    continue
                if path.is_symlink() or not path.is_file() or path.suffix.lower() not in EXTENSIONS:
                    continue
                if path.stat().st_size > self.settings.max_file_size_bytes:
                    continue
                rel = path.relative_to(root).as_posix()
                visited.add(rel)
                try:
                    raw = path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                filehash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
                if previous.get(rel) == filehash:
                    skipped += 1
                    continue
                # Line-aligned bounded chunks; no response contains unlimited source code.
                lines = raw.splitlines(keepends=True)
                chunks = ["".join(lines[i : i + 60])[:12000] for i in range(0, len(lines), 60)]
                db.execute("DELETE FROM chunks WHERE project=? AND path=?", (project, rel))
                for i, chunk in enumerate(chunks):
                    vector = None
                    if model is not None:
                        vector = json.dumps(model.encode(chunk).tolist())
                    db.execute(
                        "INSERT INTO chunks VALUES(?,?,?,?,?,?)",
                        (project, rel, i, filehash, chunk, vector),
                    )
                updated += 1
            # Do not prune unseen files if the scan was bounded by max_files.
            if len(visited) < max_files:
                for old in set(previous) - visited:
                    db.execute("DELETE FROM chunks WHERE project=? AND path=?", (project, old))
        return {
            "project": project,
            "updated_files": updated,
            "unchanged_files": skipped,
            "scanned_files": len(visited),
            "mode": "semantic" if model else "lexical",
            "scan_complete": len(visited) < max_files,
        }

    def search(self, project: str, query: str, limit: int = 10) -> dict:
        self._root(project)
        if not query.strip() or not 1 <= limit <= 50:
            raise WorkspaceError("Provide non-empty query and limit between 1 and 50.")
        model = self._model()
        query_vector = model.encode(query).tolist() if model is not None else None
        terms = set(t.lower() for t in TOKEN.findall(query))
        hits = []
        with self._connect() as db:
            for path, part, body, vec in db.execute(
                "SELECT path, part, body, vector FROM chunks WHERE project=?", (project,)
            ):
                if query_vector is not None and vec is not None:
                    vector = json.loads(vec)
                    dot = sum(a * b for a, b in zip(query_vector, vector))
                    norm = math.sqrt(sum(a * a for a in query_vector) * sum(b * b for b in vector))
                    score = dot / norm if norm else 0
                else:
                    found = set(t.lower() for t in TOKEN.findall(body))
                    score = len(terms & found) / len(terms) if terms else 0
                if score > 0:
                    hits.append((score, path, part, body))
        hits.sort(key=lambda h: (-h[0], h[1], h[2]))
        return {
            "project": project,
            "mode": "semantic" if model else "lexical",
            "results": [
                {"score": round(score, 5), "path": path, "part": part, "excerpt": body[:1200]}
                for score, path, part, body in hits[:limit]
            ],
        }
