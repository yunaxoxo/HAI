"""Regression tests for LOLCODE lexical analysis."""
import unittest

from interpreter import Interpreter
from lexer import LexicalError, tokenize, tokenize_with_locations


class LexerTests(unittest.TestCase):
    def test_program_and_variable_keywords(self):
        source = 'HAI\nWAZZUP\nI HAS A value ITZ 17\nBUHBYE\nKTHXBYE'
        self.assertEqual([t[0] for t in tokenize(source) if t[0] != 'NEWLINE'],
                         ['HAI', 'WAZZUP', 'I_HAS_A', 'IDENTIFIER', 'ITZ', 'NUMBR', 'BUHBYE', 'KTHXBYE'])

    def test_keyword_prefixes_are_identifiers(self):
        words = ['BTWextra', 'OBTWextra', 'TLDRextra', 'WINNER', 'FAILURE', 'ROBOT', 'APPLE', 'HAI2', 'WAZZUP_1']
        self.assertEqual(tokenize(' '.join(words)), [('IDENTIFIER', word, 1) for word in words])

    def test_keywords_are_case_sensitive(self):
        self.assertEqual(tokenize('hai HAI'), [('IDENTIFIER', 'hai', 1), ('HAI', 'HAI', 1)])

    def test_multiword_tokens(self):
        for word, kind in [('SUM OF', 'SUM_OF'), ('HOW IZ I', 'HOW_IZ_I'),
                           ('IF U SAY SO', 'IF_U_SAY_SO'), ('O RLY?', 'O_RLY?'),
                           ('IS NOW A', 'IS_NOW_A'), ('IM OUTTA YR', 'IM_OUTTA_YR')]:
            with self.subTest(word=word):
                self.assertEqual(tokenize(word), [(kind, word, 1)])

    def test_numeric_literals(self):
        self.assertEqual(tokenize('0 -17 17.0 -0.25 001'),
                         [('NUMBR', '0', 1), ('NUMBR', '-17', 1), ('NUMBAR', '17.0', 1),
                          ('NUMBAR', '-0.25', 1), ('NUMBR', '001', 1)])

    def test_invalid_numeric_forms(self):
        for source in ['12abc', '1_000', '1.2.3', '1.', '.5', '1e3', '--1', '١٢']:
            with self.subTest(source=source):
                with self.assertRaises(SyntaxError):
                    tokenize(source)

    def test_strings_preserve_contents(self):
        for value in ['""', '"spaces    between"', '"x:"', '"Enter a value: "',
                      '"BTW OBTW TLDR"', '"a\\b"', '"<script>alert(1)</script>"', '"café ♡"',
                      '"Line1:)Line2:>Tabbed::Colon:::"Quoted:":o"']:
            with self.subTest(value=value):
                self.assertEqual(tokenize(value), [('YARN', value, 1)])

    def test_strings_cannot_cross_physical_lines(self):
        for source in ['"missing', '"a\nb"', '"a\rb"', 'VISIBLE "line1 :)\nline2"']:
            with self.subTest(source=source):
                with self.assertRaises(SyntaxError):
                    tokenize(source)

    def test_trailing_colon_before_closing_quote_is_not_an_escape(self):
        self.assertEqual([t[1] for t in tokenize('VISIBLE "x:" + WIN + " y:"')],
                         ['VISIBLE', '"x:"', '+', 'WIN', '+', '" y:"'])

    def test_yarn_colon_escapes_and_spans(self):
        source = 'HAI\nVISIBLE "Line 1:)Line 2:>Tabbed:: :"Quoted:":o"\nKTHXBYE'
        tokens, spans = tokenize_with_locations(source)
        yarn_idx = next(i for i, t in enumerate(tokens) if t[0] == 'YARN')
        yarn_tok = tokens[yarn_idx]
        yarn_span = spans[yarn_idx]
        self.assertEqual(yarn_tok, ('YARN', '"Line 1:)Line 2:>Tabbed:: :"Quoted:":o"', 2))
        self.assertEqual(source[yarn_span['start_offset']:yarn_span['end_offset']], yarn_tok[1])
        self.assertEqual((yarn_span['line'], yarn_span['column']), (2, 9))

    def test_yarn_escape_runtime_decoding_visible_and_smoosh(self):
        outputs = []
        source = (
            'HAI\n'
            'VISIBLE "Line 1:)Line 2:>Tabbed:: :"Quoted:":o"\n'
            'VISIBLE SMOOSH "A:)" AN "B:>C::" AN ":"D:":o" MKAY\n'
            'KTHXBYE'
        )
        Interpreter(output_func=lambda text, **kw: outputs.append(text)).run_source(source)
        self.assertEqual(outputs[0], 'Line 1\nLine 2\tTabbed: "Quoted"\x07')
        self.assertEqual(outputs[1], 'A\nB\tC:"D"\x07')

    def test_inline_comments(self):
        self.assertEqual(tokenize('VISIBLE "BTW" BTW ignored\n'),
                         [('VISIBLE', 'VISIBLE', 1), ('YARN', '"BTW"', 1), ('NEWLINE', '\n', 1)])

    def test_block_comments_keep_following_line_locations(self):
        result = tokenize('HAI\n  OBTW BTW note\nanything @ "\n  TLDR BTW end\nVISIBLE 1\nKTHXBYE')
        self.assertEqual([t for t in result if t[0] != 'NEWLINE'],
                         [('HAI', 'HAI', 1), ('VISIBLE', 'VISIBLE', 5), ('NUMBR', '1', 5), ('KTHXBYE', 'KTHXBYE', 6)])

    def test_invalid_block_delimiters(self):
        for source in ['OBTW\nmissing', 'VISIBLE 1 OBTW\nx\nTLDR',
                       'OBTW extra\nx\nTLDR', 'OBTW\nx\nTLDR VISIBLE 1', 'TLDR']:
            with self.subTest(source=source):
                with self.assertRaises(SyntaxError):
                    tokenize(source)

    def test_newline_variants(self):
        expected = [('HAI', 'HAI', 1), ('NEWLINE', '\n', 1), ('KTHXBYE', 'KTHXBYE', 2)]
        for separator in ['\n', '\r\n', '\r']:
            with self.subTest(separator=repr(separator)):
                self.assertEqual(tokenize('HAI' + separator + 'KTHXBYE'), expected)

    def test_visible_separators_are_real_tokens(self):
        self.assertEqual(tokenize('VISIBLE "x:" + x'),
                         [('VISIBLE', 'VISIBLE', 1), ('YARN', '"x:"', 1), ('PLUS', '+', 1), ('IDENTIFIER', 'x', 1)])

    def test_types_preserve_parser_contract(self):
        self.assertEqual(tokenize('NOOB NUMBR NUMBAR YARN TROOF TYPE WIN FAIL'),
                         [('TYPE', word, 1) for word in ['NOOB', 'NUMBR', 'NUMBAR', 'YARN', 'TROOF', 'TYPE']] +
                         [('TROOF', 'WIN', 1), ('TROOF', 'FAIL', 1)])

    def test_whitespace_and_empty_input(self):
        self.assertEqual(tokenize(' \t'), [])
        self.assertEqual(tokenize(''), [])
        self.assertEqual(tokenize('\t  HAI'), [('HAI', 'HAI', 1)])

    def test_invalid_identifiers_and_characters(self):
        for source in ['_name', '@', 'a-b', 'éclair']:
            with self.subTest(source=source):
                with self.assertRaises(SyntaxError):
                    tokenize(source)

    def test_tuple_interface(self):
        for token in tokenize('HAI\nVISIBLE 1\nKTHXBYE'):
            self.assertIsInstance(token, tuple)
            self.assertEqual(len(token), 3)
            self.assertIsInstance(token[2], int)

    def test_source_ranges_preserve_raw_offsets_and_columns(self):
        source = 'HAI\r\n  VISIBLE "😊" + SUM OF 5 AN 3\rKTHXBYE'
        tokens, spans = tokenize_with_locations(source)
        self.assertEqual(tokens, tokenize(source))
        self.assertEqual(len(tokens), len(spans))
        for (kind, lexeme, line), span in zip(tokens, spans):
            raw = source[span["start_offset"]:span["end_offset"]]
            self.assertEqual(raw, '\r\n' if kind == 'NEWLINE' and span['end_offset'] - span['start_offset'] == 2
                             else ('\r' if kind == 'NEWLINE' and raw == '\r' else lexeme))
            self.assertEqual(span['line'], line)
        visible = next(span for token, span in zip(tokens, spans) if token[0] == 'VISIBLE')
        self.assertEqual((visible['line'], visible['column'], visible['end_column']), (2, 3, 10))
        plus = next(span for token, span in zip(tokens, spans) if token[0] == 'PLUS')
        self.assertEqual(source[plus['start_offset']:plus['end_offset']], '+')
        self.assertEqual(plus['end_column'], plus['column'] + 1)

    def test_error_retains_completed_spans_and_exact_character(self):
        with self.assertRaises(LexicalError) as thrown:
            tokenize_with_locations('HAI\nVISIBLE 1\n@')
        error = thrown.exception
        self.assertEqual((error.line, error.column), (3, 1))
        self.assertEqual((error.start_offset, error.end_offset), (14, 15))
        self.assertEqual(len(error.tokens), len(error.token_locations))
        self.assertEqual(error.tokens[-1], ('NEWLINE', '\n', 2))

    def test_unterminated_block_comment_points_to_eof(self):
        source = 'HAI\nOBTW\nnotes'
        with self.assertRaises(LexicalError) as thrown:
            tokenize_with_locations(source)
        error = thrown.exception
        self.assertEqual(error.start_offset, len(source))
        self.assertEqual(error.end_offset, len(source))
        self.assertEqual(error.end_column, error.column)

    def test_visible_plus_is_separator_not_arithmetic_syntax(self):
        self.assertIn(('PLUS', '+', 2), tokenize('HAI\nVISIBLE "hello" + 7\nKTHXBYE'))
        self.assertIn(('SUM_OF', 'SUM OF', 2), tokenize('HAI\nVISIBLE SUM OF 5 AN 3\nKTHXBYE'))

    def test_line_continuation_suppresses_newline_and_preserves_lines(self):
        for separator in ['\n', '\r\n', '\r']:
            with self.subTest(separator=repr(separator)):
                source = (
                    f'HAI{separator}'
                    f'    VISIBLE SUM OF 1 ... BTW continue{separator}'
                    f'    AN 2{separator}'
                    f'KTHXBYE'
                )
                tokens, spans = tokenize_with_locations(source)
                self.assertEqual(
                    tokens,
                    [
                        ('HAI', 'HAI', 1),
                        ('NEWLINE', '\n', 1),
                        ('VISIBLE', 'VISIBLE', 2),
                        ('SUM_OF', 'SUM OF', 2),
                        ('NUMBR', '1', 2),
                        ('AN', 'AN', 3),
                        ('NUMBR', '2', 3),
                        ('NEWLINE', '\n', 3),
                        ('KTHXBYE', 'KTHXBYE', 4),
                    ],
                )
                an_span = next(span for tok, span in zip(tokens, spans) if tok[0] == 'AN')
                self.assertEqual((an_span['line'], an_span['column']), (3, 5))

    def test_chained_line_continuations(self):
        source = 'HAI\nVISIBLE ...\n  SUM OF ...\n  1 ...\n  AN 2\nKTHXBYE'
        tokens = [t for t in tokenize(source) if t[0] != 'NEWLINE']
        self.assertEqual(
            tokens,
            [
                ('HAI', 'HAI', 1),
                ('VISIBLE', 'VISIBLE', 2),
                ('SUM_OF', 'SUM OF', 3),
                ('NUMBR', '1', 4),
                ('AN', 'AN', 5),
                ('NUMBR', '2', 5),
                ('KTHXBYE', 'KTHXBYE', 6),
            ],
        )

    def test_line_continuation_errors(self):
        invalid_cases = [
            ('VISIBLE 1 ... AN 2', 1, 11),
            ('VISIBLE 1 ....\nAN 2', 1, 11),
            ('VISIBLE 1 ...', 1, 11),
            ('VISIBLE 1 ... BTW trailing comment at EOF', 1, 11),
            ('HAI\nVISIBLE 1 ...\n  AN 2\n@', 4, 1),
        ]
        for source, expected_line, expected_col in invalid_cases:
            with self.subTest(source=source):
                with self.assertRaises(LexicalError) as thrown:
                    tokenize_with_locations(source)
                self.assertEqual((thrown.exception.line, thrown.exception.column),
                                 (expected_line, expected_col))


if __name__ == '__main__':
    unittest.main()
