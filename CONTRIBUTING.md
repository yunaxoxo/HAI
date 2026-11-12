# Contributing to HAI

HAI is a Python LOLCODE interpreter with a browser-based workbench. Keep changes focused, readable, and compatible with the existing language-processing pipeline.

## Local setup

1. Install Python 3 and open the repository root in a terminal.
2. Run `python3 -B app.py`.
3. Visit `http://127.0.0.1:8000`.

The local server uses Python's standard library and does not require npm. For the Vercel Flask adapter, install the packages in `requirements.txt` in a virtual environment.

## Tests

Run before opening a pull request:

```bash
python3 -B -m unittest discover -q
```

Optional, if Node.js is installed:

```bash
node --check frontend/app.js
```

For frontend changes, also check keyboard navigation, the **Launch editor** flow, editor and inspector interactions, and mobile screens around 320–390px. For backend or static-file changes, test the affected endpoints locally and on a Vercel Preview.

## Code and documentation

- Keep lexing in `lexer.py`, AST construction in `parser.py`, and execution in `interpreter.py`.
- Preserve the parser-compatible token representation and source-location mappings. Update tests when changing their structure.
- Keep user-interface logic in `frontend/`; do not introduce a build system unless the project needs one.
- Update [Architecture](docs/ARCHITECTURE.md) for API or data-contract changes and [Deployment](DEPLOYMENT.md) for hosting changes.
- Retain third-party license notices in `frontend/vendor/` and `frontend/icons/`.

## Pull requests

Explain **what changed, why, and how it was tested**. Before committing, review `git status --short`, `git diff --cached`, and the staged filenames. Do not commit credentials, `.env` files, caches, `node_modules`, personal/course-only files, temporary archives, or internal development conversations.

A project-wide license has not been confirmed in the reference source; coordinate licensing with the maintainers before redistributing the project's original code.
