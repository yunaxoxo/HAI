"""Checks for the tokenize/run endpoints added for the workbench."""
import unittest

from app import analyze, run_program, tokenize_source


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

    def test_analyze_and_run_reject_same_trailing_program_statement(self):
        source = 'HAI\nKTHXBYE\nVISIBLE 1'
        analysis = analyze(source)
        executed = run_program(source, [])
        for result in (analysis, executed):
            self.assertFalse(result['ok'])
            self.assertEqual(result['error']['stage'], 'parser')
            self.assertEqual((result['error']['line'], result['error']['column']), (3, 1))
            self.assertEqual(source[result['error']['start_offset']:result['error']['end_offset']], 'VISIBLE')
        self.assertEqual(executed['output'], '')
        self.assertEqual(analysis['error'], executed['error'])

    def test_analyze_run_and_tokenize_preserve_lexer_location(self):
        source = 'HAI\nVISIBLE 1\n@'
        for result in (analyze(source), run_program(source, []), tokenize_source(source)):
            self.assertFalse(result['ok'])
            self.assertEqual(result['error']['stage'], 'lexer')
            self.assertEqual((result['error']['line'], result['error']['column']), (3, 1))
            self.assertEqual((result['error']['start_offset'], result['error']['end_offset']), (14, 15))
        self.assertEqual(len(analyze(source)['tokens']), len(analyze(source)['token_locations']))

    def test_parser_error_points_to_unexpected_newline(self):
        result = analyze('HAI\nVISIBLE SUM OF 5\nKTHXBYE')
        self.assertFalse(result['ok'])
        self.assertEqual(result['error']['stage'], 'parser')
        self.assertEqual((result['error']['line'], result['error']['column']), (2, 17))
        self.assertEqual(result['error']['start_offset'], result['error']['end_offset'])

    def test_token_locations_do_not_change_parser_tuple_contract(self):
        source = 'HAI\nVISIBLE 5 + 3\nKTHXBYE'
        result = analyze(source)
        self.assertTrue(result['ok'])
        self.assertEqual(len(result['tokens']), len(result['token_locations']))
        self.assertTrue(all(len(token) == 3 for token in result['tokens']))
        i = next(i for i, token in enumerate(result['tokens']) if token[0] == 'PLUS')
        loc = result['token_locations'][i]
        self.assertEqual(source[loc['start_offset']:loc['end_offset']], '+')


if __name__ == "__main__":
    unittest.main()

