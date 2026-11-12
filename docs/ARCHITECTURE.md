# Architecture

HAI keeps the LOLCODE implementation in Python. The browser renders the editor, compiler results, and console; it does not reimplement the lexer or interpreter.

## Processing flow

```text
LOLCODE source
    ↓
lexer.py           → tokens + source locations
    ↓
parser.py          → abstract syntax tree (AST) + node ranges
    ↓
interpreter.py     → output, variable state, or diagnostics
    ↓
app.py / api/index.py  → JSON responses to frontend/app.js
```

- `lexer.py`: recognizes tokens and their locations.
- `parser.py`: builds AST nodes from parser-compatible `(kind, lexeme, line)` token triples.
- `interpreter.py`: executes supported LOLCODE constructs.
- `app.py`: local HTTP server and shared analysis/execution functions.
- `api/index.py`: Flask endpoints for Vercel.
- `frontend/`: CodeMirror editor, AST explorer, symbol table, console, and responsive interface.

## HTTP API

Requests and responses use JSON. The API enforces a 100 KB source limit.

| Endpoint | Request | Main response fields |
| --- | --- | --- |
| `POST /api/tokenize` | `{"source": "..."}` | `ok`, `tokens`, `token_locations`, or `error` |
| `POST /api/analyze` | `{"source": "..."}` | `ok`, `tokens`, `ast`, `ast_locations`, or `error` |
| `POST /api/run` | `{"source": "...", "inputs": []}` | `ok`, `output`, `symbols`, `needs_input`, `prompt`, or `error` |

Response shapes can differ on failure; check the tests before changing API fields.

## Source mapping

Tokens preserve the representation expected by the parser. The parallel `token_locations` array stores source spans with 1-based line/column positions and 0-based, half-open Unicode-codepoint offsets. `ast_locations` maps AST JSON paths to source ranges.

The frontend converts those offsets to the positions expected by CodeMirror. Selecting an AST node can highlight the corresponding source, and changed source invalidates outdated mappings. The AST graph is limited for rendering performance; the outline and JSON views allow deeper inspection.

## Execution and input

- **Local:** `run_program()` starts a subprocess with a five-second timeout.
- **Vercel:** `run_program_inline()` runs inside the Flask request process without the same hard timeout or isolation.
- **`GIMMEH`:** the browser collects answers and reruns the program with those inputs. It is not a persistent paused interpreter.
- **Symbols:** the panel shows the final available variable values, not a step-by-step execution trace.

See [Deployment](../DEPLOYMENT.md) for security implications and hosting verification.

## Static files and dependencies

`frontend/index.html`, `style.css`, `app.js`, the favicon files, and `frontend/vendor/` assets must be served by both the local server and the Flask adapter. Unknown asset paths should return 404 rather than the HTML page. CodeMirror and icon license notices must remain with the bundled files.
