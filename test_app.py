"""Integration checks for the frontend's Python API."""

import json
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path

from app import Handler


class FrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, method, path, data=None):
        connection = HTTPConnection(*self.server.server_address, timeout=5)
        try:
            body = json.dumps(data) if data is not None else None
            connection.request(method, path, body, {"Content-Type": "application/json"})
            response = connection.getresponse()
            return response.status, response.read()
        finally:
            connection.close()

    def test_assets_and_unknown_paths(self):
        for path in ("/", "/style.css", "/app.js"):
            status, body = self.request("GET", path)
            self.assertEqual(status, 200)
            self.assertTrue(body)
        self.assertEqual(self.request("GET", "/../parser.py")[0], 404)

    def test_full_sample_produces_named_ast(self):
        source = Path(__file__).with_name("source.txt").read_text()
        status, body = self.request("POST", "/api/analyze", {"source": source})
        result = json.loads(body)
        self.assertEqual(status, 200)
        self.assertTrue(result["ok"])
        self.assertEqual(result["ast"]["node"], "Program")
        self.assertTrue(result["tokens"])

    def test_syntax_errors_keep_available_tokens(self):
        for source in ("HAI\nWAZZUP\nVISIBLE 1\nBUHBYE\nKTHXBYE",
                       "HAI\nVISIBLE SUM OF 1\nKTHXBYE",
                       "HAI\nKTHXBYE\nVISIBLE 1"):
            _, body = self.request("POST", "/api/analyze", {"source": source})
            result = json.loads(body)
            self.assertFalse(result["ok"])
            self.assertEqual(result["error"]["stage"], "parser")
            self.assertTrue(result["tokens"])
            self.assertIsNone(result["ast"])

    def test_lexer_error(self):
        _, body = self.request("POST", "/api/analyze", {"source": "HAI\n@\nKTHXBYE"})
        result = json.loads(body)
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["stage"], "lexer")

    def test_invalid_request(self):
        for payload in ({"source": 42}, {}, []):
            self.assertEqual(self.request("POST", "/api/analyze", payload)[0], 400)
        self.assertEqual(self.request("POST", "/api/analyze", {"source": "x" * 100001})[0], 413)

    def test_http_token_locations_and_error_contract(self):
        source = 'HAI\nVISIBLE 5 + 3\nKTHXBYE'
        for endpoint in ('/api/tokenize', '/api/analyze'):
            status, body = self.request('POST', endpoint, {'source': source})
            result = json.loads(body)
            self.assertEqual(status, 200)
            self.assertEqual(len(result['tokens']), len(result['token_locations']))
            i = next(i for i, tok in enumerate(result['tokens']) if tok[0] == 'PLUS')
            location = result['token_locations'][i]
            self.assertEqual(source[location['start_offset']:location['end_offset']], '+')
        status, body = self.request('POST', '/api/analyze', {'source': 'HAI\n@\nKTHXBYE'})
        self.assertEqual(status, 200)
        self.assertEqual((json.loads(body)['error']['line'], json.loads(body)['error']['column']), (2, 1))

    def test_http_run_checks_complete_program(self):
        status, body = self.request('POST', '/api/run', {'source': 'HAI\nKTHXBYE\nVISIBLE 1'})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)['error']['stage'], 'parser')


if __name__ == "__main__":
    unittest.main()
