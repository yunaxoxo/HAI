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

