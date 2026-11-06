# Maintenance boundaries and baseline

## Ownership recorded before implementation

This review began on `main` at `9c66af7`, with a clean tracked working tree
and empty index. The pre-existing untracked `project-testcases-fixed/` folder
contains ten course programs and a specification PDF. Preserve it unchanged;
redistribution permission is unknown. No AGENTS.md instructions were found.

| Area | Paths | Change authority |
| --- | --- | --- |
| Lexer | `lexer.py`, new lexer tests | Functional fixes and regression tests |
| Frontend | `frontend/` | Presentation and interaction changes |
| Shared adapter | `app.py`, `test_app.py` | UI/API integration only; preserve existing analysis contract |
| Groupmate logic | `parser.py`, `interpreter.py` | Inspect and report defects; do not change algorithms |
| Shared sample | `source.txt` | Preserve |
| Reference materials | `project-testcases-fixed/` | Local verification only; preserve originals |
| Configuration | `.gitignore` | Tracking hygiene |
| Documentation | `README.md`, `docs/` | Verified public development information |

No separate semantic analyzer, dependency manifest, build pipeline, deployment
configuration, or license file exists. Python uses the standard library;
the frontend is plain HTML/CSS/JavaScript.

## Original baseline

- Existing API suite: **5/5 passed** with a temporary localhost socket.
- No independent lexer tests or browser tests existed.
- Supplied programs: **2/10** passed combined lexical/syntax analysis using
  Python universal-newline reads; the other eight stopped in the lexer.
- Confirmed original probes: CRLF rejected, `BTWextra` discarded as a comment,
  unterminated block comments returned as identifiers, `12abc` split into two
  tokens, raw newlines accepted in strings, code following TLDR discarded,
  plus separators rejected, variable-section markers classified as identifiers.
- Plain colons in supplied strings were rejected by the string regex.
- `NOOB` was classified as TYPE; changing that contract needs coordination
  because the parser consumes TYPE in cast targets.
- Frontend: large promotional heading, green palette, equal fixed panels,
  no standalone lexical analysis, no execution integration, no symbol table.
- Static page behavior: source changes invalidate results; requests use revision
  checks; tabs have arrow-key navigation. Preserve these useful properties.

Original source/reference SHA-256 hashes were recorded in temporary local
review files for end-of-review preservation checks. No commits are created by
this review.

## After the lexer and workbench pass

- Lexer: 17 regression tests in `test_lexer.py` (12 failures and 6 errors
  before the fixes, all passing after). Tokens keep the `(kind, lexeme, line)`
  contract; lexical errors are `SyntaxError` subclasses carrying line/column.
- Workbench: `app.py` gained `/api/tokenize` and `/api/run`; `/api/analyze` is
  unchanged. Run executes `interpreter.py` in a child process with a 5-second
  limit, so the interpreter itself is untouched. Checks live in `test_workbench.py`.
- Supplied programs: all 10 tokenize. 4 parse as-is (01, 02, 06, 09); with
  `PLUS` tokens ignored, 9 parse (see `docs/PARSER_FINDINGS.md`).
- Not verified: rendered appearance in a browser, and mobile layouts.

