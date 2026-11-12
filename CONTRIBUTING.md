# Contributing to HAI

HAI is a small, single-file LOLCODE interpreter/workbench. Keep changes understandable and preserve the separation between source analysis, execution, and UI presentation.

## Development setup

1. Install Python 3 and clone the repository.
2. Run `python3 -B app.py` from the repository root.
3. Visit `http://127.0.0.1:8000`.

No JavaScript package installation is necessary. For the hosted Flask adapter, install its dependency in a virtual environment using `python3 -m pip install -r requirements.txt`.

## Before a pull request

```bash
python3 -B -m unittest discover -q
node --check frontend/app.js  # if Node.js is available
```

Test the affected interactions manually. For UI changes, inspect both a desktop viewport and a phone-sized viewport (including 320px), check keyboard focus and shortcuts, and try editor, AST navigation, and input prompts. For routing/static-asset changes, check both local and Vercel Preview responses, especially Content-Type and HTTP status.

Keep changes focused. Explain any changes to AST shape, token locations, parser compatibility, error formatting, or execution limits in the PR description. Update [Architecture](docs/ARCHITECTURE.md) when changing API contracts. Preserve the bundled third-party license notices.

## Public repository hygiene

Do not commit passwords, `.env` files, personal or class-only materials, generated previews, ZIP archives, local `node_modules`, `.vercel` project metadata, or internal conversation/handoff notes. Review `git status --short` and `git diff --cached` before committing.

This repository does not declare a project-wide software license yet. Contact the maintainers before reusing or redistributing its original code beyond the rights provided by law.
