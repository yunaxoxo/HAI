"""Independent lexer regressions; course references stay local and unchanged."""
import unittest

from lexer import tokenize


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
                      '"BTW OBTW TLDR"', '"a\\b"', '"<script>alert(1)</script>"', '"café ♡"']:
            with self.subTest(value=value):
                self.assertEqual(tokenize(value), [('YARN', value, 1)])

    def test_strings_cannot_cross_physical_lines(self):
        for source in ['"missing', '"a\nb"', '"a\rb"']:
            with self.subTest(source=source):
                with self.assertRaises(SyntaxError):
                    tokenize(source)

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


if __name__ == '__main__':
    unittest.main()

