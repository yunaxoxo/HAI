# HAI.

A small, source-linked language workbench for **LOLCODE**. Write and run programs, inspect lexer tokens, navigate the actual parser AST, and trace errors back to the source.

The interface is designed as a source-linked compiler explorer rather than a general-purpose IDE. It opens directly to the editor, without a timed splash or decorative animation. A full-height code buffer sits beside a split inspector and console. Its deliberately neutral surfaces, single-level controls, and small visual separators let the source and compiler output carry the hierarchy. Compiler results come from the Python interpreter, not simulated frontend data.

## Quick start

Requires **Python 3** with the standard library. No npm install, CDN connection, or separate frontend build is required.

```bash
python3 -B app.py
```

Open **http://127.0.0.1:8000**. The server binds to localhost and is intended for local development, not public internet hosting.

### Workbench features

- **Editor:** CodeMirror-based editor with LOLCODE syntax highlighting, line numbers, indentation, active source selection, and diagnostics in the gutter.
- **Tokenize:** inspect a compact table of lexemes, categories, and `line:column` positions. Filter tokens by text or type, then select a row to navigate to its source location.
- **Analyze:** inspect the parser's real AST. Switch between a keyboard-navigable outline, a pannable/zoomable tree graph, and raw JSON. Each node displays actual values or operators when available. Select an AST node to reveal the corresponding source expression; selecting source also highlights its most specific matching AST node.
- **AST exploration:** use **Find node** in Outline mode to locate node types, operators, names, or values. Press Enter/Shift+Enter to cycle matches, and Escape to clear search. Collapse/Expand folds branches. Selecting a node reveals a parent path, original properties, child count, and precise source span where available. Graph mode centers its initial view on the selected node (or program root).
- **Source mapping:** AST paths and source spans are supplied by the parser. Maps are cleared after edits so outdated results cannot silently point to wrong code.
- **Run:** execute locally in a bounded child process; see output, final variable values, and stage-specific diagnostics. The console’s Preset input disclosure accepts one preset value per line for `GIMMEH`, with a Clear input control and confirmation. Interactive input requests appear as a minimal console input row, with the program prompt, one field, and a Send action.
- **File handling:** open `.lol` or `.txt` files, load samples directly from the keyboard-accessible Examples menu, and download the current program with a chosen filename. HAI asks before replacing unsaved source; the operating system still controls file-picking and download destinations.
- **Navigation and shortcuts:** switch between AST, Tokens, and Symbols; use Output and Problems for execution feedback. A low-profile **Shortcuts** button in the footer opens a built-in shortcut reference. The status bar displays source location without duplicating editor actions.
- **Responsive layout:** full-height editor beside a split inspector/output rail on desktop. On phones, Code / Explore / Output are full-width views. The top bar stays compact, with the Examples menu available when needed. Analyze and Tokenize lead to Explore on success; errors open Problems and its source navigation returns to Code.

Useful shortcuts: **Cmd/Ctrl + Enter** to run; **Cmd/Ctrl + S** to open the download dialog; **Cmd/Ctrl + O** to open a source file; **Shift + /** (the `?` key) or **Cmd/Ctrl + /** or the footer **Shortcuts** action to show all shortcuts; **Tab** to indent; **Shift + Tab** to outdent; **Esc** to leave the editor. The AST search uses **Enter / Shift + Enter** to move between matches.

`Clear results` in the footer clears compiler results, **not** your program. The separate `Clear input` control clears only preset input values. Save downloads a `.lol` file; it does not automatically write back to an imported file.

## Backend and API

The frontend sends JSON to three endpoints served by `app.py`:

| Route | Description |
| --- | --- |
| `POST /api/tokenize` | Lexer tokens and their source locations |
| `POST /api/analyze` | Tokens, serialized AST, and a separate AST source-location map |
| `POST /api/run` | Execution output, variables, input requests, and errors |

The lexer and parser continue to use their original three-value token tuples. The API additionally returns `token_locations`. `ast_locations` maps JSON paths such as `$.body[0].values[0]` to source spans. A location uses **1-based line and column** and **0-based, half-open Unicode codepoint offsets**. The editor converts those offsets to JavaScript UTF-16 indices.

The app preserves the supplied language grammar: `VISIBLE` operands may be separated by `+`; arithmetic addition is written `SUM OF x AN y`.

For details about the API and frontend boundaries, see [Architecture](docs/ARCHITECTURE.md).

## Running tests

```bash
python3 -B -m unittest discover -q
node --check frontend/app.js
```

`node --check` is optional and requires Node.js; running the workbench does **not** require Node.

The Python suite covers lexer behavior, interpreter integration, complete-program validation, runtime errors, and source mapping. Test coverage is not proof of compliance with every LOLCODE variant.

You can also run the command-line interpreter on a source file:

```bash
python3 -B interpreter.py source.txt
```

## Project layout

```text
app.py                   Python HTTP server and API adapter
lexer.py                 Tokenizer
parser.py                AST construction and source locations
interpreter.py           LOLCODE evaluator
frontend/index.html      Workbench structure and accessible controls
frontend/style.css       Design tokens, layout, responsive treatments
frontend/app.js          Code editor integration, API state, AST navigation
frontend/vendor/         Bundled CodeMirror editor and MIT license
docs/ARCHITECTURE.md    Public technical architecture

test_*.py                Regression and API tests
```

Locally, the runtime executes programs in a fresh Python child process. Interactive `GIMMEH` replays the accumulated input answers; it is **not** a paused debugger. The symbol inspector shows the **final visible variable snapshot**, not a time-travel trace. Very large AST graphs are capped for visual performance; the outline remains available for full traversal.

## Third-party software

The included **CodeMirror 5.58.3** editor is distributed under the MIT license. See `frontend/vendor/LICENSE.md`. This standalone bundle was chosen to keep the workbench fully runnable offline, without npm dependencies. It is **not** React, Vite, or CodeMirror 6.

## Deploying to Vercel

The repository also includes `vercel.json`, `requirements.txt`, and `api/index.py` for a Python serverless deployment. Import the repository as a Vercel project with the **repository root** as its Root Directory, and leave the framework preset at Other. The bundled editor assets do not need a JavaScript build.

Vercel uses an in-process interpreter adapter instead of the local child-process runner. That path does **not** enforce the same five-second local subprocess timeout; the hosting platform limits execution separately. Verify your deployed endpoint behavior and resource limits before making it publicly available. This release has been tested locally but has not been live-deployed to Vercel. See [Deployment guide](DEPLOYMENT.md) for Git and CLI instructions and verification steps.
