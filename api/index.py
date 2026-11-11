from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from flask import Flask, jsonify, request, send_from_directory
from app import analyze, tokenize_source, run_program_inline, MAX_SOURCE_BYTES

FRONTEND = ROOT / "frontend"
app = Flask(__name__)


@app.get("/")
def index():
    return send_from_directory(FRONTEND, "index.html")


@app.get("/style.css")
def style():
    return send_from_directory(FRONTEND, "style.css")


@app.get("/app.js")
def app_js():
    return send_from_directory(FRONTEND, "app.js")


@app.get("/vendor/<path:filename>")
def vendor(filename: str):
    return send_from_directory(FRONTEND / "vendor", filename)


@app.post("/api/analyze")
def api_analyze():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("source"), str):
        return jsonify({"message": "Send a JSON object with a source string."}), 400
    if len(data["source"].encode("utf-8")) > MAX_SOURCE_BYTES:
        return jsonify({"message": "Choose a program smaller than 100 KB."}), 413
    return jsonify(analyze(data["source"]))


@app.post("/api/tokenize")
def api_tokenize():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("source"), str):
        return jsonify({"message": "Send a JSON object with a source string."}), 400
    if len(data["source"].encode("utf-8")) > MAX_SOURCE_BYTES:
        return jsonify({"message": "Choose a program smaller than 100 KB."}), 413
    return jsonify(tokenize_source(data["source"]))


@app.post("/api/run")
def api_run():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("source"), str):
        return jsonify({"message": "Send a JSON object with a source string."}), 400
    if len(data["source"].encode("utf-8")) > MAX_SOURCE_BYTES:
        return jsonify({"message": "Choose a program smaller than 100 KB."}), 413
    inputs = data.get("inputs", [])
    if not isinstance(inputs, list) or not all(isinstance(item, str) for item in inputs):
        return jsonify({"message": "inputs must be a list of strings."}), 400
    return jsonify(run_program_inline(data["source"], inputs))


@app.get("/<path:path>")
def catch_all(path: str):
    candidate = FRONTEND / path
    if candidate.is_file():
        return send_from_directory(FRONTEND, path)
    return send_from_directory(FRONTEND, "index.html")
