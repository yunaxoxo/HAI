"""Checks for the tokenize/run endpoints added for the workbench."""
import unittest

from app import run_program, tokenize_source


class WorkbenchTests(unittest.TestCase):
    def test_tokenize_reports_location_on_error(self):
        result = tokenize_source('HAI\n"oops')
        self.assertFalse(result["ok"])
        self.assertEqual((result["error"]["line"], result["error"]["column"]), (2, 1))

    def test_run_captures_output_and_symbols(self):
        result = run_program('HAI\nI HAS A x ITZ 4\nVISIBLE SUM OF x AN 1\nKTHXBYE\n', [])
        self.assertTrue(result["ok"])
        self.assertEqual(result["output"], "5\n")
        self.assertIn("x", [item["name"] for item in result["symbols"]])

    def test_run_feeds_gimmeh_inputs(self):
        source = 'HAI\nI HAS A n\nGIMMEH n\nVISIBLE SUM OF n AN 1\nKTHXBYE\n'
        self.assertEqual(run_program(source, ["41"])["output"], "n? 41\n42\n")

    def test_run_pauses_for_live_input(self):
        source = 'HAI\nI HAS A n\nGIMMEH n\nVISIBLE SUM OF n AN 1\nKTHXBYE\n'
        waiting = run_program(source, [])
        self.assertTrue(waiting["ok"])
        self.assertTrue(waiting["needs_input"])
        self.assertEqual(waiting["prompt"], "n? ")
        self.assertFalse(run_program(source, ["41"])["needs_input"])

    def test_run_reports_stage_of_failure(self):
        self.assertEqual(run_program('HAI\nVISIBLE\nKTHXBYE', [])["error"]["stage"], "parser")
        self.assertEqual(run_program('HAI\nVISIBLE "x\nKTHXBYE', [])["error"]["stage"], "lexer")

    def test_run_stops_runaway_loops(self):
        result = run_program('HAI\nIM IN YR l\nIM OUTTA YR l\nKTHXBYE\n', [])
        self.assertFalse(result["ok"])


if __name__ == "__main__":
    unittest.main()

