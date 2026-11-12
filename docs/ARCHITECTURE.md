# Architecture

HAI is a single-page frontend backed by Python language-processing modules. The JavaScript editor displays results; it is **not** a second compiler.

## Components

```text
Browser: HTML + CSS + app.js + bundled CodeMirror
  |       |        |
  |       |        +-- POST /api/run ------> Python interpreter
  |       +----------- POST /api/analyze --> lexer + parser + AST
  +------------------- POST /api/tokenize -> lexer

Local hosting: app.py (Python standard-library HTTP server)
Vercel hosting: api/index.py (Flask adapter)
```

- `lexer.py` produces lexer tokens and optional source locations.
- `parser.py` consumes `(kind, lexeme, line)` token triples to build the AST.
- `interpreter.py` executes the AST.
- `app.py` validates requests, builds API responses, and runs programs in a timeout-bound child process locally.
- `api/index.py` adapts the same API to Flask for Vercel. It calls the in-process runner (see runtime limitations below).
- `frontend/app.js` manages editor state, AST presentation, console, dialogs, and responsive views.

## API

All three routes accept JSON objects and return JSON:

| Route | Input | Result |
| --- | --- | --- |
| `POST /api/tokenize` | `{ "source": "..." }` | tokens and `token_locations` |
| `POST /api/analyze` | `{ "source": "..." }` | tokens, serialized AST, `ast_locations`, or diagnostics |
| `POST /api/run` | `{ "source": "...", "inputs": [] }` | output, final symbols, input request, or error |

Program source is limited to 100 KB by the HTTP API. Some API error details depend on the stage that produced them.

## Source-location contract

Tokens remain compatible with the parser's `(kind, lexeme, line)` structure. The associated `token_locations` array contains aligned spans with 1-based line/column numbers and 0-based, half-open **Unicode codepoint** offsets. Example:

```json
{
  "line": 2, "column": 9, "end_line": 2, "end_column": 22,
  "start_offset": 12, "end_offset": 25
}
```

`ast_locations` is a separate map keyed by AST JSON paths, such as `$.body[0].values[0]`. These paths are valid only for the current analysis result. Frontend selection translates Python codepoint offsets to CodeMirror's JavaScript UTF-16 offsets. When the source changes, stale source maps and diagnostics are invalidated.

The UI supports an expandable AST outline, a limited graph view, and raw JSON. Source-to-AST navigation selects the most specific matching node with a known span. Missing source spans are not guessed.

## Runtime and UI limitations

- **Local**: `run_program()` uses a child process with a five-second deadline.
- **Vercel**: `run_program_inline()` does not have equivalent process isolation or a hard per-program timeout. Do not assume the serverless platform is a secure sandbox for untrusted programs.
- **`GIMMEH`**: the frontend re-runs with collected answers; it doesn't pause/resume a live interpreter process.
- **Symbols**: the inspector shows the available final variable snapshot, not execution history.
- **Large ASTs**: graph view is limited for rendering performance; use Outline for full exploration.

## Static assets

`frontend/` is the source of the workbench and local assets. Both the local handler and the Flask adapter must serve `favicon.ico`, `favicon.svg`, `favicon-32x32.png`, and `apple-touch-icon.png` with image MIME types, as well as editor CSS/JS and CodeMirror vendor files. Their URLs are absolute (`/favicon.ico`, etc.); unknown files must not silently return the homepage HTML.

The included `vercel.json` routes frontend requests to the Flask adapter. Any additional assets need server route coverage and deployment verification.

## Maintenance

For changes to language behavior, add/adjust regression tests. For UI changes, verify keyboard navigation and phone-width layouts. Preserve the CodeMirror MIT and Lucide/Feather icon notices in their respective `frontend/` subfolders.
