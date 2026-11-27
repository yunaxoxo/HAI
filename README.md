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

Select **Run** to print `8`, **Tokenize** to inspect lexical tokens, or **Structure** to explore the AST.

On Windows, use the same command (`python -B app.py`, or `py -3 -B app.py`). The workbench runs entirely offline: CodeMirror and the icons are bundled, so no internet connection or `pip install` is needed.

## Language behavior notes

- **Integer division:** `QUOSHUNT OF` on two `NUMBR`s returns a `NUMBR` truncated toward zero (`QUOSHUNT OF -7 AN 2` is `-3`); if either operand is a `NUMBAR` the result is a `NUMBAR`.
- **`NOOB`:** `VISIBLE` and `SMOOSH` print an uninitialized variable as `NOOB` (the official `10_functions.lol` relies on this for `GTFO` functions). A `NOOB` can be cast to `TROOF` implicitly, but using it as a number raises an error; explicit `MAEK` / `IS NOW A` casts give `0`, `0.0`, `FAIL` or the empty `YARN`.
- **Function calls:** `I IZ ... MKAY` is the documented form. The closing `MKAY` is optional for a flat call so the official `10_functions.lol` runs as written, but a call nested as a non-final argument needs its own `MKAY` (`I IZ f YR I IZ g YR 4 MKAY AN YR 1 MKAY`). Functions only see their own parameters and locals, and `GTFO` or reaching `IF U SAY SO` returns `NOOB`.
- **Declarations:** every variable must be declared once in `WAZZUP`; assigning an undeclared name, declaring a name twice, or defining a function twice is an error. `I HAS A t ITZ NUMBR` stores the type name.
- **`IT`:** only expression statements (including a lone literal or variable) set `IT`; operands of `VISIBLE`, assignments, declarations, loop conditions and case labels do not.
- **Comparison:** there is no implicit casting, so `5` and `5.0` (or `"5"`) are different.
- **Switch-case:** a matching `OMG` runs and falls through the following cases until `GTFO`; the `OMGWTF` default runs only when no case matches.
- **Input:** `GIMMEH` shows a `name? ` prompt, and reading past the end of the input is a runtime error. One statement per line is expected, but a `,` or a second statement on a line is tolerated.
- **`YARN` to number:** only digits, `-` and `.` are accepted (`"-3"`, `".5"`); `"+5"`, `"1_000"`, `"1e3"` and the empty string are errors, while surrounding spaces from `GIMMEH` are trimmed.
- **`NUMBAR` to `YARN`:** values are truncated (not rounded) to two decimal places.
- **Strings:** `YARN` literals support the escapes `:)` (newline), `:>` (tab), `:o` (bell), `:"` (quote) and `::` (colon).

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
