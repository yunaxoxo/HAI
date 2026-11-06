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
- **Tokenize** shows the lexer output; click a token row to jump to its line.
- **Analyze** adds the syntax tree, or the lexer/parser error.
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

Known gap: `VISIBLE a + b` (the `+` separator) is tokenized but not yet
accepted by the parser. See `docs/PARSER_FINDINGS.md`.

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

Expected results on the current code:

| File | Result |
| --- | --- |
| `01_variables`, `02_gimmeh`, `06_comparison`, `09_loops` | `OK` |
| `03_arith`, `04_smoosh_assign`, `05_bool`, `07_ifelse`, `10_functions` | `parser` error on the `+` separator |
| `08_switch` | `parser` error on a bare variable statement |

All six failures come from the two open issues in `docs/PARSER_FINDINGS.md`.
Once the parser accepts `+` and bare variable statements, all ten programs
should print `OK`. Update this table and the findings doc when that happens.

To test a single program, open it in the workbench (**Open**, then **Run**), or run:

```sh
python3 -B interpreter.py project-testcases-fixed/09_loops.lol
```

```sh
python3 -B -m unittest test_lexer.py test_workbench.py test_app.py
```

## Layout

- `lexer.py`, `parser.py`, `interpreter.py`: the language pipeline.
- `app.py` and `frontend/`: the local web workbench.
- `docs/`: maintenance notes and findings.

## Repository housekeeping

`.gitignore` excludes Python caches, virtual environments, build output,
local environment files, and operating system metadata. Keep source code,
sample programs, tests, and documentation under version control.

