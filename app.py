"""Local web interface for the lexer, parser, and interpreter. Run with python -B app.py."""

import json
import subprocess
import sys
from dataclasses import fields, is_dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from interpreter import Interpreter
from lexer import tokenize
from parser import Parser

FRONTEND = Path(__file__).parent / "frontend"
MAX_SOURCE_BYTES = 100_000
RUN_TIMEOUT_SECONDS = 5
MAX_OUTPUT_CHARACTERS = 100_000


def ast_to_dict(value):
    """Keep node names so the syntax tree is easier to read in the browser."""
    if is_dataclass(value):
        return {"node": type(value).__name__, **{
            field.name: ast_to_dict(getattr(value, field.name))
            for field in fields(value)
        }}
    if isinstance(value, list):
        return [ast_to_dict(item) for item in value]
    if isinstance(value, dict):
        return {key: ast_to_dict(item) for key, item in value.items()}
    return value


def analyze(source):
    tokens = []
    stage = "lexer"
    try:
        tokens = tokenize(source)
        stage = "parser"
        parser = Parser(tokens)
        program = parser.parse()
        # The parser currently stops after the program and trailing functions.
        if not parser.is_at_end():
            token = parser.peek()
            raise SyntaxError(f"Line {token[2]}: Unexpected token '{token[1]}' after program.")
        return {"ok": True, "tokens": tokens, "ast": ast_to_dict(program)}
    except (SyntaxError, RecursionError, ValueError) as error:
        message = str(error)
        if isinstance(error, RecursionError):
            message = "Expressions are nested too deeply. Try simplifying the program."
        return {"ok": False, "tokens": tokens, "ast": None,
                "error": {"stage": stage, "message": message}}


# --- Tokenize only ---
def tokenize_source(source):
    """Runs just the lexer so tokens can be inspected without parsing.

    Args:
        source: The LOLCODE program text.

    Returns:
        A dict with "ok", "tokens", and (on failure) an "error" holding the
        stage, message, and the line/column when the lexer knows them.
    """
    try:
        return {"ok": True, "tokens": tokenize(source)}
    except SyntaxError as error:
        details = {"stage": "lexer", "message": str(error)}
        for key in ("line", "column"):
            if hasattr(error, key):
                details[key] = getattr(error, key)
        return {"ok": False, "tokens": list(getattr(error, "tokens", [])), "error": details}


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
        tokens = tokenize(request["source"])
        stage = "parser"
        program = Parser(tokens).parse()
        stage = "runtime"
        interpreter.execute(program)
    except NeedInput as waiting:
        result = {"ok": True, "error": None, "needs_input": True, "prompt": waiting.prompt}
    except (SyntaxError, RuntimeError, ZeroDivisionError, RecursionError, ValueError) as error:
        result = {"ok": False, "needs_input": False, "error": {"stage": stage, "message": str(error)}}

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

