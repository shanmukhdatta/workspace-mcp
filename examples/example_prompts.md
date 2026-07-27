# Sample Prompts

These are prompts you can paste into Claude Desktop (with `workspace-mcp` connected) to see the tools in action. All of them result in real files on disk inside your configured `workspace_root`.

---

## 🌟 Master Prompt (Full-Potential Demonstration)

Copy and paste this master prompt into Claude Desktop to exercise all major Workspace MCP tool capabilities in a single flow:

```text
Using the workspace MCP, create a new project called [project-name]. Set up the following structure: create a src/ directory, add starter files inside it ([file1], [file2]), and create a top-level README.md and .gitignore.

Once the files exist, append a notes section to the README, then update [file1] with the core logic for [feature].

Search the project for any TODO or FIXME comments using find_text. Find all files matching *.[ext] using search_files.

Rename [file2] to [new-name], then move it into a new docs/ directory.

Generate the project tree, generate a proper README, and generate a CLOUD.md log summarizing what was built.

Finally, validate the workspace configuration, and list the contents of the project root to confirm everything is in place.
```

---

## 1. Scaffold a full-stack project

> Using the workspace tools, create a project called "ExpenseTracker" — a FastAPI backend with a `/expenses` REST API and a React frontend for viewing/adding expenses. Create the full folder structure, write starter code for both the backend and frontend, and generate the README and CLOUD.md when you're done.

## 2. Minimal single-purpose script project

> Create a project called "CsvCleaner" with just `src` and `tests` folders (no default scaffold). Write a Python script in `src/clean.py` that strips whitespace and drops empty rows from a CSV, plus a pytest test in `tests/test_clean.py`. Generate the README.

## 3. Explore an existing project

> List everything inside the "ExpenseTracker" project, then search for every Python file and show me any file that contains the text "TODO".

## 4. Safe, confirmation-gated edits

> Open `ExpenseTracker/backend/main.py`, show me its contents, then replace the placeholder health-check response with a real one and write it back.

(Claude will call `read_file`, then `write_file` — if the file already exists it will surface a `CONFIRMATION_REQUIRED` error first and ask you before retrying with `confirm=true`.)

## 5. Rename and clean up

> Rename the "CsvCleaner" project to "DataCleaner", then delete the old "ExpenseTracker" project entirely — but check with me before doing anything destructive.

## 6. Validate before you build

> Before creating anything, validate the workspace and tell me what file types are allowed and what the size limit is.

## 7. Regenerate documentation only

> Regenerate the PROJECT_TREE.md and README.md for "DataCleaner" without touching any code files.

## 8. Multi-project audit

> Search across the entire workspace for any file containing the text "API_KEY" so I can make sure I haven't hardcoded a secret anywhere.
