# lolcode-interpreter

An interpreter for LOLCODE, written in Python.

## Status
- [x] Lexer
- [x] Parser
- [x] Initial command-line interpreter (still in development)
- [x] Web workbench (editor, tokens, syntax tree, run output, symbols)

## Requirements

Python 3 with the standard library. No additional packages are required.

## Command-line usage

Run the included sample program:

```sh
python3 -B interpreter.py source.txt
```

You can replace `source.txt` with the path to your own LOLCODE file. Running
without a filename also uses `source.txt`. The sample prompts for input near
the end through `GIMMEH`.

The initial interpreter implements variables, assignments, typecasts,
arithmetic and Boolean expressions, comparisons, string concatenation,
console input/output, conditionals, switches, loops, and function calls.
It is still in development; full LOLCODE compatibility is not yet verified.

To inspect the sample's tokens or syntax tree separately:

```sh
python3 -B lexer.py
python3 -B parser.py
```

## Web workbench

Start the local frontend with Python (no additional packages needed):

```sh
python3 -B app.py
```

Open http://127.0.0.1:8000 in your browser. Stop the server with Ctrl+C.

- Write LOLCODE or load one of the included examples.
- **Tokenize** shows lexer output with line and column; click a token row (or press Enter/Space when focused) to select its exact source lexeme.
- **Analyze** adds an expandable syntax tree with source-linked nodes. Select
  an AST node to select its exact source range; selecting a source expression
  highlights the smallest matching AST node. The original JSON remains under
  **View raw AST JSON**. Errors with known locations include Go to source.
- **Run** executes the program and shows its output and variables. When the
  program reaches `GIMMEH`, the Output panel shows a live prompt: type a value and
  press Enter. The *Preset input* box is optional and answers prompts in advance.
  Runs stop after 5 seconds.
- Ctrl+Enter (Cmd+Enter on macOS) runs. In the editor, Esc then Tab moves focus out.
- Open a `.lol` or `.txt` file, and save your editor contents as `playground.lol`.

Run uses the command-line interpreter in a separate process. To ask for input
live, the program is rerun from the start with each new answer added (no server
sessions), so every answer is replayed deterministically. Keep a saved copy
of your code before closing or refreshing the page. The server listens on
localhost for local use.

The course's `+` separator in `VISIBLE a + b` is supported. It is distinct
from arithmetic addition, written `SUM OF a AN b`. Both Analyze and Run reject
unexpected tokens after `KTHXBYE`, while still allowing the trailing functions
supported by the course specification. See `docs/PARSER_FINDINGS.md` for the
verified status of previously reported parser concerns.

For future source-to-AST UI work, the lexer exposes `tokenize_with_locations()`.
`/api/tokenize` and `/api/analyze` return an additional `token_locations` array
aligned with the existing `tokens` tuples. It contains 1-based line/column and
0-based, half-open Python Unicode codepoint offsets. The frontend converts
codepoint offsets to textarea UTF-16 offsets before selecting the lexeme.
The parser's three-field token contract remains unchanged. The parser now
accepts optional aligned token locations and records token-derived source spans
for constructed AST nodes. Analyze adds a separate `ast_locations` map, keyed
by JSON paths such as `$.body[0].values[0]`; the AST JSON itself is unchanged.
Locations refer to **one analyzed revision**, not stable identifiers across edits.
The frontend clears mappings when the source changes.

Parser errors can pinpoint the unexpected token or the end of a line (an empty
span); errors with a known earlier location retain that location rather than
receiving invented columns. Runtime errors inside expressions receive the
innermost failing AST node's source range when available. See
`docs/COMPILER_ATLAS_FOUNDATION.md` for details and limitations.

## Tests

### Checking the course test programs

The ten course programs are in `project-testcases-fixed/`. That folder is
git-ignored, because the course materials may not be redistributable. Each
contributor keeps a local copy in the repository root. The folder has no
expected-output files, so this check only reports whether each program
tokenizes, parses, and runs. It does not check that the output is correct.

Run this from the repository root:

```sh
python3 -B - <<'EOF'
from pathlib import Path
from app import run_program

for path in sorted(Path('project-testcases-fixed').glob('*.lol')):
    source = path.read_bytes().decode('utf-8')
    answers = []
    for _ in range(10):
        result = run_program(source, answers)
        if not result['needs_input']:
            break
        answers.append('4')   # feeds 4 to every GIMMEH
    status = 'OK' if result['ok'] else f"{result['error']['stage']}: {result['error']['message']}"
    print(path.name, '->', status)
EOF
```

How it works:

- `run_program` is the same function behind the workbench's Run button. It runs
  the program in a separate process with a 5-second limit.
- Each time a program reaches `GIMMEH`, `run_program` returns `needs_input`. The
  loop adds the answer `4` and runs the program again, up to 10 times.
- A status of `OK` means the program ran to the end without an error. Anything
  else prints the stage (`lexer`, `parser`, or `runtime`) and the message.
- Programs that do arithmetic on their input need numeric answers, which is why
  the script feeds `4`. A non-numeric answer fails with "Cannot convert ... to a
  number."
- On Windows PowerShell, `<<'EOF'` does not work. Save the Python part as
  `check_testcases.py` and run `python -B check_testcases.py`.

Verified against the ten **user-supplied** course programs (November 2026):
all 10 tokenize and parse. All 10 complete without reported runtime errors when
provided with enough preset `"4"` answers. This verifies execution completion,
**not** correctness of expected output (the ZIP contains no expected-output
reference files). The supplied course programs are not included in this
repository distribution.

The earlier `PLUS`-separator and standalone-variable parser findings have
already been resolved in `parser.py` and are now marked as historical in
`docs/PARSER_FINDINGS.md`. Do not change the parser based on those stale findings.

To test a single program, open it in the workbench (**Open**, then **Run**), or run:

```sh
python3 -B interpreter.py project-testcases-fixed/09_loops.lol
```

```sh
python3 -B -m unittest discover -q
```

## Layout

- `lexer.py`, `parser.py`, `interpreter.py`: the language pipeline.
- `app.py` and `frontend/`: the local web workbench.
- `docs/`: maintenance notes and findings.

## Repository housekeeping

`.gitignore` excludes Python caches, virtual environments, build output,
local environment files, and operating system metadata. Keep source code,
sample programs, tests, and documentation under version control.

