# Project Tree: workspace-mcp

Generated: 2026-07-27 12:32:56 UTC

```
workspace-mcp/
├── docs/
│   ├── API.md
│   ├── ARCHITECTURE.md
│   ├── CLIENT_CONFIG.md
│   ├── CONFIGURATION.md
│   ├── DEVELOPER_GUIDE.md
│   ├── EXTENSION_GUIDE.md
│   ├── INSTALL.md
│   └── QUICKSTART.md
├── examples/
│   ├── claude_desktop_config.json
│   └── example_prompts.md
├── src/
│   └── workspace_mcp/
│       ├── config/
│       │   ├── __init__.py
│       │   └── settings.py
│       ├── logging/
│       │   ├── __init__.py
│       │   └── logger.py
│       ├── models/
│       │   ├── __init__.py
│       │   └── schemas.py
│       ├── services/
│       │   ├── __init__.py
│       │   ├── directory_service.py
│       │   ├── doc_service.py
│       │   ├── file_service.py
│       │   ├── project_service.py
│       │   └── search_service.py
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── _common.py
│       │   ├── directory_tools.py
│       │   ├── doc_tools.py
│       │   ├── file_tools.py
│       │   ├── project_tools.py
│       │   ├── search_tools.py
│       │   └── validation_tools.py
│       ├── utils/
│       │   ├── __init__.py
│       │   └── pathsec.py
│       ├── __init__.py
│       └── server.py
├── tests/
│   ├── conftest.py
│   ├── test_directory_service.py
│   ├── test_doc_service.py
│   ├── test_error_handling.py
│   ├── test_file_service.py
│   ├── test_path_validation.py
│   ├── test_project_service.py
│   ├── test_search_service.py
│   └── test_workspace_restriction.py
├── .gitignore
├── CLOUD.md
├── pyproject.toml
├── README.md
└── workspace_mcp.config.example.yaml
```
