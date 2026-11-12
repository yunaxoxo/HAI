# HAI.

**A browser-based LOLCODE workbench.** Write and execute programs, inspect tokens and syntax trees, and follow compiler errors back to the source.

HAI is a lightweight editor and compiler explorer—not a general-purpose IDE. It works locally without a frontend build step or an internet connection.

## Getting started

You need **Python 3**. From the repository root:

```bash
python3 -B app.py
```

Open **http://127.0.0.1:8000** in a browser. On your first visit in a tab, choose **Launch editor** after the short welcome screen.

Try this program:

```lolcode
HAI
VISIBLE SUM OF 5 AN 3
KTHXBYE
```

Select **Run** to print `8`, **Tokenize** to inspect lexical tokens, or **Analyze** to explore the syntax tree. No account, npm installation, or hosted service is required for local use.

## Features

- **Source editor:** syntax highlighting, line numbers, editable LOLCODE source, open/download `.lol` files, and built-in examples.
- **Compiler inspector:** tokens, searchable and expandable AST outline, graphical AST view, raw JSON, and final variable values.
- **Source navigation:** select an AST node to highlight its source; inspect errors in the editor and Problems tab.
- **Program execution:** Output console, preset input, and interactive `GIMMEH` prompts.
- **Keyboard access:** `Cmd/Ctrl + Enter` to run, `Cmd/Ctrl + O` to open, `Cmd/Ctrl + S` to download, and `?` or `Cmd/Ctrl + /` to open the shortcuts reference.
- **Responsive interface:** desktop split views and dedicated **Code / Explore / Output** views on small screens.

**Save** downloads a file; it does not overwrite the file you originally opened. Interactive input re-executes the program with accumulated answers; this isn't a step-through debugger.

## For contributors

The application uses **Python** for lexing, parsing, and execution, plus **HTML/CSS/vanilla JavaScript** and a locally bundled CodeMirror 5 editor. No React or JavaScript build system is required.

```bash
python3 -B -m unittest discover -q
node --check frontend/app.js  # optional: requires Node.js
```

See [Contributing](CONTRIBUTING.md) for developer setup, [Architecture](docs/ARCHITECTURE.md) for data flow and API contracts, [Deployment](DEPLOYMENT.md) for Vercel, and the [release checklist](docs/RELEASE_CHECKLIST.md) for pre-merge verification.

## Repository structure

```text
HAI/
├── app.py                # local HTTP server and API
├── lexer.py              # LOLCODE tokenizer and locations
├── parser.py             # AST construction and source ranges
├── interpreter.py        # runtime
├── api/index.py          # Flask adapter for Vercel
├── frontend/             # HTML, CSS, JS, favicon and offline editor assets
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   ├── favicon.svg
│   ├── favicon.ico
│   ├── favicon-32x32.png
│   ├── apple-touch-icon.png
│   ├── vendor/           # CodeMirror and its license
│   └── icons/            # inline icon attribution
├── docs/ARCHITECTURE.md
├── docs/RELEASE_CHECKLIST.md
├── test_*.py             # regression and HTTP tests
├── source.txt            # bundled sample and test fixture
├── requirements.txt      # hosted Flask dependency
├── vercel.json           # Vercel routing
├── .vercelignore
├── .gitignore
├── CONTRIBUTING.md
└── DEPLOYMENT.md
```

## Scope and security

The local runner has a five-second subprocess timeout. **The Vercel adapter executes code in-process and does not provide the same timeout or isolation.** Review execution/resource safeguards before enabling unrestricted public use; see [Deployment](DEPLOYMENT.md).

HAI implements the LOLCODE subset supported by this interpreter. Its syntax and behavior should be checked against the tests rather than assumed to cover all LOLCODE dialects.

## Third-party acknowledgments

- [CodeMirror 5](frontend/vendor/LICENSE.md) — MIT license, bundled for offline editing.
- [Lucide and Feather icons](frontend/icons/LICENSE.md) — applicable ISC/MIT notices for inline toolbar glyphs.

A project-wide license has **not** been selected in this package; the maintainers should agree on one before advertising the project as open source.
