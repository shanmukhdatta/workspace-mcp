from __future__ import annotations

import pytest

from workspace_mcp.models.schemas import NotFoundError
from workspace_mcp.services.file_service import FileService
from workspace_mcp.services.search_service import SearchService


@pytest.fixture(autouse=True)
def _populate(file_service: FileService):
    file_service.create_file("proj/backend/main.py", "def main():\n    print('hello world')\n")
    file_service.create_file("proj/backend/utils.py", "def helper():\n    return 42\n")
    file_service.create_file("proj/frontend/app.js", "console.log('hello world');\n")
    file_service.create_file("proj/README.md", "# Proj\nhello world in docs\n")


class TestSearchFiles:
    def test_glob_search_by_extension(self, search_service: SearchService):
        results = search_service.search_files("*.py")
        assert any(r.endswith("main.py") for r in results)
        assert any(r.endswith("utils.py") for r in results)
        assert not any(r.endswith(".js") for r in results)

    def test_glob_search_missing_root_raises(self, search_service: SearchService):
        with pytest.raises(NotFoundError):
            search_service.search_files("*.py", rel_root="does/not/exist")


class TestFindText:
    def test_find_text_across_files(self, search_service: SearchService):
        matches = search_service.find_text("hello world")
        paths = {m.path for m in matches}
        assert any("main.py" in p for p in paths)
        assert any("app.js" in p for p in paths)
        assert any("README.md" in p for p in paths)

    def test_find_text_extension_filter(self, search_service: SearchService):
        matches = search_service.find_text("hello world", extensions=[".py"])
        assert all(m.path.endswith(".py") for m in matches)

    def test_find_text_case_insensitive_by_default(self, search_service: SearchService):
        matches = search_service.find_text("HELLO WORLD")
        assert len(matches) > 0

    def test_find_text_case_sensitive(self, search_service: SearchService):
        matches = search_service.find_text("HELLO WORLD", case_sensitive=True)
        assert len(matches) == 0
