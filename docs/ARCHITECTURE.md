# Workbench architecture

This document describes the public API and source-mapping contract. It is a technical reference for maintaining the workbench.

## Execution path

```text
Browser workbench
  ├── POST /api/tokenize  ──> tokenize_with_locations()
  ├── POST /api/analyze   ──> Lexer -> Parser -> ast_to_dict()
  └── POST /api/run       ──> bounded child process -> Interpreter
```

`app.py` serves only explicitly allowed frontend assets and API routes on `127.0.0.1`. Python language logic stays in `lexer.py`, `parser.py`, and `interpreter.py`. The workbench does not implement a second parser in JavaScript.

The frontend is one dependency-free application script plus a bundled copy of CodeMirror 5 (MIT). No bundler or npm is needed for normal use. The editor's tokenizer is only a **syntax-coloring heuristic**. Backend tokens and AST are authoritative.

## Source positions

`tokenize_with_locations(source)` returns `(tokens, locations)` with aligned indices. Each token retains the original `(kind, lexeme, line)` tuple consumed by the parser; each location supplies:

```json
{
  "line": 2,
  "column": 9,
  "end_line": 2,
  "end_column": 22,
  "start_offset": 12,
  "end_offset": 25
}
```

The four line/column fields are 1-based, and the offsets are Python Unicode **codepoint** offsets in a half-open interval (`[start_offset, end_offset)`). When using CodeMirror, the browser converts these offsets to JavaScript **UTF-16** character indices, including in source containing emoji.

The serializer returns an AST without adding properties inside existing nodes. Instead, `/api/analyze` returns a separate dictionary `ast_locations`, keyed by the original JSON property paths. For example `$.body[0].values[0]` identifies the first print value in the first top-level statement.

Paths are stable only **within one analysis response**. They are not durable identifiers across edits. When source changes, the frontend clears tokens, AST, mappings, diagnostics and output; it requires analysis again. Do not guess missing spans.

## Tree navigation and selection

`frontend/app.js` traverses the returned AST to build records containing a node, its JSON path, children, parent and descriptive primitive fields. It deliberately skips arrays and dictionaries that are not themselves AST nodes while recursively finding nested child nodes.

The UI presents:

- **Outline:** a nested list with collapsible branches, keyboard-focusable node buttons, and selected-node properties presented in labeled rows.
- **Graph:** a limited hierarchical layout drawn in the browser with HTML buttons and SVG connectors. Node selection maps to source; double-clicking a parent folds its branch. Zoom controls are visual only; they do not alter AST data.
- **Raw JSON:** unmodified backend serialization.

When selecting an editor span, the UI picks the smallest AST node whose source span contains the selection. When clicking a node, it selects the known source span in the editor. Hover highlights are previews and never scroll the editor.

## Diagnostics

API errors contain the actual stage and message, with source ranges only if supplied. Source-aware errors are drawn as underlined editor ranges and gutter markers. If the backend only knows a line, the UI highlights that line; it does not manufacture a character-accurate range.

Problems and output are separate console tabs. Diagnostics with no known source location (such as network failures) do not receive arbitrary editor gutter markers. When a line is known but the exact character span is not, the row is highlighted without an exact-position squiggle. Run first performs analysis if the source has changed, ensuring AST results correspond to the execution input. Both API requests use the current source revision to ignore stale results.

## Runtime limitations

- The process timeout is 5 seconds.
- Interactive input reruns the program with all accumulated answers. There is no live instruction pointer or step-debugging session.
- Symbol results represent the runtime's available final variables. They are not a history of changes or a full scope inspector.
- Graph mode renders up to 210 visible nodes for performance; use Outline for large programs.
- User-supplied source is never inserted into the page as HTML.

## Updating the frontend

The server serves these static routes: `/`, `/style.css`, `/app.js`, `/vendor/codemirror.css`, and `/vendor/codemirror.js`. If adding asset files, extend the explicit allowlist in `app.py` and update the integration tests. Do not introduce a directory-traversal-capable generic file handler.

`frontend/style.css` defines the interface vocabulary: a near-black editor, a graphite inspector, muted sage for source mappings, and warm red for diagnostics. The source editor occupies the full height of the left workspace, while the AST/token/variable inspector shares the right rail with a console below it. There is no simulated project/file explorer because this is a single-file language workbench. On narrow screens, focused Editor / Inspect / Console views preserve working space. Test keyboard, mouse, and small-screen navigation before changing the layout.

The vendored CodeMirror files remain MIT-licensed; preserve their license notice when updating them. If moving to React/Vite/CodeMirror 6 in a future iteration, preserve the API contract and end-to-end source-mapping tests. That migration is **not included in this release**.

## Presentation and deployment

The source/editor surface remains independent from Python language processing. The console input disclosure accepts line-separated `GIMMEH` answers and can be cleared without changing the source. The status bar shows the current compiler/execution state and the editor position.

For Vercel, `api/index.py` exposes matching routes through Flask and `vercel.json` routes requests to that entry point. This uses the `run_program_inline()` adapter; unlike local `run_program()`, it does not use a subprocess timeout. The hosted runtime depends on platform limits and should be separately verified.
