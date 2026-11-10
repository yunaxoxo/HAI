"""Regression coverage for source-to-AST mapping and precise diagnostics.

These are opt-in API annotations; grammar and AST dataclasses stay compatible.
"""
import unittest
from app import analyze, run_program
from interpreter import Interpreter
from lexer import tokenize, tokenize_with_locations
from parser import Parser


class SourceMappingTests(unittest.TestCase):
    def test_exact_nested_arithmetic_spans(self):
        source = 'HAI\nVISIBLE SUM OF 5 AN 3\nKTHXBYE'
        result = analyze(source)
        self.assertTrue(result['ok'])
        self.assertEqual(result['ast']['body'][0]['node'], 'PrintStmt')
        expr = '$.body[0].values[0]'
        self.assertEqual(result['ast']['body'][0]['values'][0]['node'], 'ArithExpr')
        spans = result['ast_locations']
        self.assertEqual(source[spans[expr]['start_offset']:spans[expr]['end_offset']], 'SUM OF 5 AN 3')
        self.assertEqual(source[spans[expr+'.left']['start_offset']:spans[expr+'.left']['end_offset']], '5')
        self.assertEqual(source[spans[expr+'.right']['start_offset']:spans[expr+'.right']['end_offset']], '3')
        self.assertEqual(source[spans['$.body[0]']['start_offset']:spans['$.body[0]']['end_offset']], 'VISIBLE SUM OF 5 AN 3')

    def test_maps_all_nodes_in_nested_structures(self):
        source = '''HAI
WAZZUP
I HAS A x ITZ 2
BUHBYE
x
O RLY?
YA RLY
VISIBLE SUM OF x AN 3
NO WAI
VISIBLE 0
OIC
KTHXBYE'''
        result = analyze(source)
        self.assertTrue(result['ok'], result.get('error'))
        paths = result['ast_locations']
        ast = result['ast']
        def check(node, path='$'):
            if isinstance(node, dict):
                if 'node' in node:
                    self.assertIn(path, paths, path)
                    loc = paths[path]
                    self.assertLess(loc['start_offset'], loc['end_offset'])
                    self.assertTrue(source[loc['start_offset']:loc['end_offset']])
                for key, item in node.items():
                    check(item, f'{path}.{key}')
            elif isinstance(node, list):
                for i, item in enumerate(node):
                    check(item, f'{path}[{i}]')
        check(ast)
        # The expression preceding O RLY? is retained as part of Conditional.
        conditional = paths['$.body[1]']
        self.assertEqual(source[conditional['start_offset']], 'x')
        self.assertTrue(source[conditional['start_offset']:conditional['end_offset']].endswith('OIC'))

    def test_ast_shape_does_not_contain_metadata_fields(self):
        result = analyze('HAI\nVISIBLE 1\nKTHXBYE')
        self.assertTrue(result['ok'])
        self.assertEqual(set(result['ast']), {'node', 'body', 'functions'})
        self.assertNotIn('source', result['ast'])
        self.assertIn('ast_locations', result)

    def test_unicode_and_crlf_offsets(self):
        source = 'HAI\r\nVISIBLE "😊"\r\nKTHXBYE'
        result = analyze(source)
        self.assertTrue(result['ok'])
        path = '$.body[0].values[0]'
        loc = result['ast_locations'][path]
        self.assertEqual(source[loc['start_offset']:loc['end_offset']], '"😊"')
        self.assertEqual((loc['line'], loc['column']), (2, 9))

    def test_standalone_parser_does_not_require_positions(self):
        parser = Parser(tokenize('HAI\nVISIBLE 7\nKTHXBYE'))
        result = parser.parse()
        self.assertEqual(result.body[0].values[0].value, 7)
        self.assertEqual(parser.node_spans, {})
        with self.assertRaises(ValueError):
            Parser([('HAI','HAI',1)], [])

    def test_parser_error_exact_unexpected_token(self):
        source = 'HAI\nVISIBLE SUM OF 5\nKTHXBYE'
        result = analyze(source)
        self.assertFalse(result['ok'])
        error = result['error']
        self.assertEqual(error['stage'], 'parser')
        self.assertEqual((error['line'], error['column']), (2, 17))
        self.assertEqual(error['start_offset'], error['end_offset'])
        self.assertEqual(result['ast_locations'], {})

    def test_runtime_error_points_to_smallest_failing_node(self):
        cases = [
            ('HAI\nVISIBLE mystery\nKTHXBYE', 'mystery', 'Undefined variable'),
            ('HAI\nVISIBLE QUOSHUNT OF 5 AN 0\nKTHXBYE', 'QUOSHUNT OF 5 AN 0', 'Division by zero'),
            ('HAI\nVISIBLE SUM OF "nope" AN 2\nKTHXBYE', 'SUM OF "nope" AN 2', 'Cannot convert'),
        ]
        for source, fragment, message in cases:
            with self.subTest(fragment=fragment):
                result = run_program(source, [])
                self.assertFalse(result['ok'])
                self.assertEqual(result['error']['stage'], 'runtime')
                error = result['error']
                self.assertIn(message, error['message'])
                self.assertEqual(source[error['start_offset']:error['end_offset']], fragment)

    def test_cli_and_api_both_reject_trailing_statement(self):
        source = 'HAI\nKTHXBYE\nVISIBLE 7'
        with self.assertRaisesRegex(SyntaxError, 'Unexpected token'):
            Interpreter().run_source(source)
        self.assertEqual(analyze(source)['error']['stage'], 'parser')
        self.assertEqual(run_program(source, [])['error']['stage'], 'parser')

    def test_original_tuple_interface_intact(self):
        source = 'HAI\nVISIBLE "hi" + 7\nKTHXBYE'
        tokens, locations = tokenize_with_locations(source)
        self.assertEqual(tokens, tokenize(source))
        self.assertTrue(all(len(token) == 3 for token in tokens))
        self.assertEqual(len(tokens), len(locations))


if __name__ == '__main__':
    unittest.main()
