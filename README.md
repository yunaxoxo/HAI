# HAI.

**An interactive LOLCODE interpreter and language workbench.**

HAI was developed as a course requirement for **CMSC 124 (Design and Implementation of Programming Languages)** at the **University of the Philippines Los Baños (UPLB)**.

Designed to explore how programming languages work under the hood, HAI lets users write, execute, and debug LOLCODE programs while inspecting lexical tokens, an abstract syntax tree (AST), variables in a symbol table, and errors linked to their source code. It brings programming-language theory and practical implementation together in one accessible, interactive environment.

## Getting started

**Requirement:** Python 3. No frontend build step or npm installation is needed.

From the project root:

```bash
python3 -B app.py
```

Open **http://127.0.0.1:8000** in a browser. On the initial visit in a tab, choose **Launch editor**.

Try:

```lolcode
HAI
VISIBLE SUM OF 5 AN 3
KTHXBYE
```

Select **Run** to print `8`, **Tokenize** to inspect lexical tokens, or **Analyze** to explore the AST.

## Features

- **Editor:** LOLCODE highlighting, built-in examples, and opening or downloading `.lol` files.
- **Language inspection:** tokens, searchable AST outline, graphical and JSON views, and a symbol table.
- **Source-linked diagnostics:** inspect syntax/runtime problems and navigate between AST nodes and code.
- **Execution:** console output, preset input, and interactive `GIMMEH` prompts.
- **Responsive controls:** desktop workbench and mobile **Code**, **Explore**, and **Output** views, with keyboard shortcuts accessible through **Shortcuts** or `?`.

**Note:** Save downloads the current source; it does not overwrite an opened file. Input prompts rerun the program with collected answers rather than pausing a step-through debugger. HAI supports the LOLCODE features implemented in this project, not necessarily every dialect.

## Developing HAI

The backend is written in **Python** (`lexer.py`, `parser.py`, `interpreter.py`, `app.py`). The frontend uses **HTML, CSS, vanilla JavaScript**, and bundled **CodeMirror 5**. Vercel hosting uses the Flask adapter in `api/index.py`.

Run the tests from the repository root:

```bash
python3 -B -m unittest discover -q
```

With Node.js installed, you can also run `node --check frontend/app.js`. No Node.js dependencies are needed to run the website locally.

| Guide | Contents |
| --- | --- |
| [Contributing](CONTRIBUTING.md) | Local setup, tests, and contribution practices |
| [Architecture](docs/ARCHITECTURE.md) | Interpreter pipeline, APIs, and source mapping |
| [Deployment](DEPLOYMENT.md) | Local and Vercel deployment, verification, and limitations |
| [Release checklist](docs/RELEASE_CHECKLIST.md) | Checks before merging or releasing |

## Repository overview

```text
app.py                  Local HTTP server and API
lexer.py / parser.py    Language analysis and syntax tree
interpreter.py          LOLCODE execution
api/index.py            Flask adapter for Vercel
frontend/               Browser UI, favicons, and bundled editor assets
test_*.py               Automated regression tests
docs/                   Architecture and release documentation
```

## Limits and acknowledgments

The local runner applies a five-second subprocess timeout. **The Vercel runner executes programs in-process without equivalent isolation or a hard program timeout.** Review execution safeguards before making it publicly accessible without restrictions. See [Deployment](DEPLOYMENT.md).

The repository includes license notices for [CodeMirror](frontend/vendor/LICENSE.md) and [Lucide/Feather icons](frontend/icons/LICENSE.md). A project-wide software license should be agreed upon by the maintainers before inviting unrestricted reuse.
