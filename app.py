"""Local web interface for the lexer, parser, and interpreter. Run with python -B app.py."""

import json
import re
import subprocess
import sys
from dataclasses import fields, is_dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from interpreter import Interpreter
from lexer import tokenize_with_locations
from parser import Parser

FRONTEND = Path(__file__).parent / "frontend"
MAX_SOURCE_BYTES = 100_000
RUN_TIMEOUT_SECONDS = 5
MAX_OUTPUT_CHARACTERS = 100_000


def ast_to_dict(value, spans=None, output_locations=None, path="$"):
    """Serialize AST without changing its existing JSON shape.

    Optional ``output_locations`` collects a parallel mapping from stable JSON
    paths to token-derived source spans, so old API consumers still work.
    Paths identify nodes within this single analysis result, not across edits.
    """
    if is_dataclass(value):
        if spans is not None and output_locations is not None:
            loc = spans.get(id(value))
            if loc is not None:
                output_locations[path] = dict(loc)
        return {"node": type(value).__name__, **{
            field.name: ast_to_dict(getattr(value, field.name), spans,
                                    output_locations, f"{path}.{field.name}")
            for field in fields(value)
        }}
    if isinstance(value, list):
        return [ast_to_dict(item, spans, output_locations, f"{path}[{i}]")
                for i, item in enumerate(value)]
    if isinstance(value, dict):
        return {key: ast_to_dict(item, spans, output_locations, f"{path}.{key}")
                for key, item in value.items()}
    return value


def add_parser_error_location(error, parser, locations):
    """Point to the unexpected token, or a zero-width EOF position.

    A location is attached only when it represents where the parse actually
    stopped. We do not guess where a node should have been inserted.
    """
    if getattr(error, "start_offset", None) is not None or not locations:
        return
    index = parser.position
    if index < len(locations):
        selected = locations[index].copy()
        if parser.tokens[index][0] == "NEWLINE":
            # The offending event is the line break, not the next line.
            selected["end_line"] = selected["line"]
            selected["end_column"] = selected["column"]
            selected["end_offset"] = selected["start_offset"]
    else:
        previous = locations[-1]
        selected = {"line": previous["end_line"],
                    "column": previous["end_column"],
                    "end_line": previous["end_line"],
                    "end_column": previous["end_column"],
                    "start_offset": previous["end_offset"],
                    "end_offset": previous["end_offset"]}
    # A custom parser error might point to a previously consumed token; do
    # not overwrite its explicit line with a misleading current-token span.
    match = re.match(r"Line (\d+):", str(error))
    if match and int(match.group(1)) != selected["line"]:
        return
    for key, value in selected.items():
        setattr(error, key, value)


def error_details(error, stage):
    """Preserve known locations without inventing exact parser/runtime columns."""
    details = {"stage": stage, "message": str(error)}
    for key in ("line", "column", "end_line", "end_column",
                "start_offset", "end_offset"):
        value = getattr(error, key, None)
        if value is not None:
            details[key] = value
    # The existing parser raises plain SyntaxError with a line in its message.
    # This is a line-only fallback; it is NOT a reliable exact source range.
    if "line" not in details:
        match = re.match(r"Line (\d+):", details["message"])
        if match:
            details["line"] = int(match.group(1))
    return details


def parse_complete(tokens, locations):
    """Parse the entire source, returning the AST and its location metadata."""
    parser = Parser(tokens, locations)
    try:
        program = parser.parse()
        if not parser.is_at_end():
            token = parser.peek()
            raise SyntaxError(f"Line {token[2]}: Unexpected token '{token[1]}' after program.")
        return program, parser.node_spans
    except SyntaxError as error:
        add_parser_error_location(error, parser, locations)
        raise


def analyze(source):
    tokens, locations = [], []
    stage = "lexer"
    try:
        tokens, locations = tokenize_with_locations(source)
        stage = "parser"
        program, spans = parse_complete(tokens, locations)
        ast_locations = {}
        ast = ast_to_dict(program, spans, ast_locations)
        return {"ok": True, "tokens": tokens, "token_locations": locations,
                "ast": ast, "ast_locations": ast_locations}
    except (SyntaxError, RecursionError, ValueError) as error:
        if isinstance(error, RecursionError):
            error = ValueError("Expressions are nested too deeply. Try simplifying the program.")
        return {"ok": False, "tokens": list(getattr(error, "tokens", tokens)),
                "token_locations": list(getattr(error, "token_locations", locations)),
                "ast": None, "ast_locations": {}, "error": error_details(error, stage)}


# --- Tokenize only ---
def tokenize_source(source):
    """Inspect the lexer without asking the parser to accept the program."""
    try:
        tokens, locations = tokenize_with_locations(source)
        return {"ok": True, "tokens": tokens, "token_locations": locations}
    except SyntaxError as error:
        return {"ok": False, "tokens": list(getattr(error, "tokens", [])),
                "token_locations": list(getattr(error, "token_locations", [])),
                "error": error_details(error, "lexer")}


# --- Run (child process side) ---
class NeedInput(Exception):
    """Raised when GIMMEH wants a value that was not supplied yet."""

    def __init__(self, prompt):
        super().__init__(prompt)
        self.prompt = prompt


def run_in_child():
    """Executes one program inside the child process and prints a JSON result.

    The request arrives on stdin as JSON ({"source", "inputs"}). Program output
    is captured instead of printed, so the JSON stays the only thing on stdout.

    Returns:
        None. The result is written to stdout.
    """
    request = json.loads(sys.stdin.read())
    pending_inputs = list(request.get("inputs", []))
    captured = []
    interpreter = Interpreter()
    result = {"ok": True, "error": None, "needs_input": False}

    def fake_output(text="", end="\n"):
        captured.append(f"{text}{end}")

    def fake_input(prompt=""):
        if not pending_inputs:
            raise NeedInput(prompt)
        answer = pending_inputs.pop(0)
        captured.append(f"{prompt}{answer}\n")
        return answer

    interpreter.output, interpreter.input = fake_output, fake_input
    stage = "lexer"
    try:
        tokens, locations = tokenize_with_locations(request["source"])
        stage = "parser"
        program, spans = parse_complete(tokens, locations)
        interpreter.node_spans = spans
        stage = "runtime"
        interpreter.execute(program)
    except NeedInput as waiting:
        result = {"ok": True, "error": None, "needs_input": True, "prompt": waiting.prompt}
    except (SyntaxError, RuntimeError, ZeroDivisionError, RecursionError, ValueError) as error:
        result = {"ok": False, "needs_input": False,
                  "error": error_details(error, stage)}

    result["output"] = "".join(captured)[:MAX_OUTPUT_CHARACTERS]
    result["symbols"] = [
        {"name": name, "type": interpreter.cast(value, "TYPE"), "value": interpreter.display(value)}
        for name, value in interpreter.variables.items()
    ]
    print(json.dumps(result))


# --- Run (server side) ---
def run_program(source, inputs):
    """Runs a program in a throwaway Python process with a time limit.

    Args:
        source: The LOLCODE program text.
        inputs: A list of strings handed out one by one to GIMMEH.

    Returns:
        A dict with "ok", "output", "symbols", "needs_input" (True when GIMMEH
        is waiting for another value, with its "prompt"), and an "error" on failure.
    """
    try:
        finished = subprocess.run(
            [sys.executable, "-B", str(Path(__file__).resolve()), "--run-child"],
            input=json.dumps({"source": source, "inputs": inputs}),
            capture_output=True, text=True, timeout=RUN_TIMEOUT_SECONDS,
            cwd=str(Path(__file__).parent))
        return json.loads(finished.stdout)
    except subprocess.TimeoutExpired:
        message = f"Program ran longer than {RUN_TIMEOUT_SECONDS} seconds, so it was stopped."
    except (ValueError, OSError):
        message = "The runner crashed before finishing. Check the terminal for details."
    return {"ok": False, "needs_input": False, "output": "", "symbols": [],
            "error": {"stage": "runtime", "message": message}}


class Handler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        assets = {"/": ("index.html", "text/html"),
                  "/style.css": ("style.css", "text/css"),
                  "/app.js": ("app.js", "text/javascript")}
        asset = assets.get(self.path.split("?", 1)[0])
        if asset is None:
            self.send_error(404)
            return
        body = (FRONTEND / asset[0]).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", asset[1] + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path not in ("/api/analyze", "/api/tokenize", "/api/run"):
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= MAX_SOURCE_BYTES:
                self.send_json({"message": "Choose a program smaller than 100 KB."}, 413)
                return
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict) or not isinstance(data.get("source"), str):
                raise ValueError("Expected a source string.")
        except (ValueError, UnicodeDecodeError):
            self.send_json({"message": "Send a JSON object with a source string."}, 400)
            return
        if self.path == "/api/tokenize":
            self.send_json(tokenize_source(data["source"]))
        elif self.path == "/api/run":
            inputs = data.get("inputs", [])
            if not isinstance(inputs, list) or not all(isinstance(item, str) for item in inputs):
                self.send_json({"message": "inputs must be a list of strings."}, 400)
                return
            self.send_json(run_program(data["source"], inputs))
        else:
            self.send_json(analyze(data["source"]))


if __name__ == "__main__":
    if "--run-child" in sys.argv:
        run_in_child()
        sys.exit(0)
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    print("LOLCODE Workbench: http://127.0.0.1:8000", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

