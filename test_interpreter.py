"""Regression tests for the LOLCODE interpreter (execution semantics)."""
import unittest

from interpreter import Interpreter


def run(body, wazzup="", inputs=(), functions=""):
    """Run a program and return what VISIBLE printed, one entry per call."""
    decls = f"WAZZUP\n{wazzup}BUHBYE\n" if wazzup else ""
    source = f"{functions}HAI\n{decls}{body}KTHXBYE\n"
    out, queue = [], iter(inputs)
    Interpreter(input_func=lambda prompt="": next(queue),
                output_func=lambda text="", **kw: out.append(text)).run_source(source)
    return out


class InterpreterTests(unittest.TestCase):
    # --- output ---
    def test_visible_casts_and_concatenates_operands(self):
        self.assertEqual(run('VISIBLE "a" + 1 + WIN + 2.5\n'), ["a1WIN2.5"])

    def test_visible_bang_suppresses_newline(self):
        out = []
        Interpreter(output_func=lambda text="", **kw: out.append((text, kw))).run_source(
            'HAI\nVISIBLE "a"!\nKTHXBYE\n')
        self.assertEqual(out[0][0], "a")
        self.assertNotEqual(out[0][1].get("end", "\n"), "\n")

    def test_smoosh(self):
        self.assertEqual(run('VISIBLE SMOOSH "a" AN 1 AN WIN MKAY\n'), ["a1WIN"])

    def test_yarn_escapes(self):
        self.assertEqual(run('VISIBLE "a:)b:>c::d:"e:o"\n'), ['a\nb\tc:d"e\x07'])

    # --- arithmetic ---
    def test_arithmetic_operators(self):
        for expr, expected in [("SUM OF 1 AN 2", "3"), ("DIFF OF 5 AN 8", "-3"),
                               ("PRODUKT OF 3 AN 4", "12"), ("MOD OF 7 AN 3", "1"),
                               ("BIGGR OF 2 AN 9", "9"), ("SMALLR OF 2 AN 9", "2"),
                               ("SUM OF 1 AN 2.5", "3.5")]:
            with self.subTest(expr=expr):
                self.assertEqual(run(f"VISIBLE {expr}\n"), [expected])

    def test_nested_arithmetic(self):
        self.assertEqual(run("VISIBLE SUM OF 1 AN PRODUKT OF 2 AN 3\n"), ["7"])

    def test_division_by_zero_is_an_error(self):
        for expr in ("QUOSHUNT OF 1 AN 0", "MOD OF 1 AN 0"):
            with self.subTest(expr=expr), self.assertRaises(RuntimeError):
                run(f"VISIBLE {expr}\n")

    @unittest.skip("#10: QUOSHUNT OF two NUMBRs should return a NUMBR")
    def test_quoshunt_of_numbrs_is_integer_division(self):
        self.assertEqual(run("VISIBLE QUOSHUNT OF 7 AN 2\n"), ["3"])

    # --- variables ---
    def test_declare_assign_and_read(self):
        self.assertEqual(run("x R SUM OF x AN 1\nVISIBLE x\n", "I HAS A x ITZ 4\n"), ["5"])

    def test_undeclared_variable_is_an_error(self):
        with self.assertRaises(RuntimeError):
            run("VISIBLE nope\n")

    def test_it_holds_last_expression(self):
        self.assertEqual(run("SUM OF 2 AN 3\nVISIBLE IT\n"), ["5"])

    def test_typecasts(self):
        self.assertEqual(run('VISIBLE MAEK "12" NUMBR\nVISIBLE MAEK 3.9 NUMBR\n'), ["12", "3"])
        self.assertEqual(run("n IS NOW A NUMBAR\nVISIBLE n\n", "I HAS A n ITZ 2\n"), ["2.0"])

    @unittest.skip("#12: NUMBAR to YARN should truncate to two decimals")
    def test_numbar_to_yarn_truncates_to_two_decimals(self):
        self.assertEqual(run("VISIBLE MAEK 3.14159 YARN\n"), ["3.14"])

    # --- input ---
    def test_gimmeh_reads_a_yarn(self):
        self.assertEqual(run("GIMMEH n\nVISIBLE SUM OF n AN 1\n", "I HAS A n\n", ["41"]), ["42"])

    # --- booleans & comparisons ---
    def test_boolean_operators(self):
        for expr, expected in [("BOTH OF WIN AN FAIL", "FAIL"), ("EITHER OF WIN AN FAIL", "WIN"),
                               ("WON OF WIN AN WIN", "FAIL"), ("NOT FAIL", "WIN"),
                               ("ALL OF WIN AN WIN AN FAIL MKAY", "FAIL"),
                               ("ANY OF FAIL AN FAIL AN WIN MKAY", "WIN")]:
            with self.subTest(expr=expr):
                self.assertEqual(run(f"VISIBLE {expr}\n"), [expected])

    def test_comparisons(self):
        for expr, expected in [("BOTH SAEM 2 AN 2", "WIN"), ("BOTH SAEM 2 AN 3", "FAIL"),
                               ("DIFFRINT 2 AN 3", "WIN"), ("BIGGR OF 1 AN 2", "2")]:
            with self.subTest(expr=expr):
                self.assertEqual(run(f"VISIBLE {expr}\n"), [expected])

    # --- control flow ---
    def test_if_else(self):
        body = "BOTH SAEM x AN 1\nO RLY?\nYA RLY\nVISIBLE \"yes\"\nNO WAI\nVISIBLE \"no\"\nOIC\n"
        self.assertEqual(run(body, "I HAS A x ITZ 1\n"), ["yes"])
        self.assertEqual(run(body, "I HAS A x ITZ 2\n"), ["no"])

    def test_switch_with_break_and_default(self):
        body = ("WTF?\nOMG 1\nVISIBLE \"one\"\nOMG 2\nVISIBLE \"two\"\nGTFO\n"
                "OMGWTF\nVISIBLE \"other\"\nOIC\n")
        self.assertEqual(run("x\n" + body, "I HAS A x ITZ 2\n"), ["two"])
        self.assertEqual(run("x\n" + body, "I HAS A x ITZ 9\n"), ["other"])

    @unittest.skip("no issue yet: a matching OMG should fall through to later cases until GTFO/OIC (spec p.5)")
    def test_switch_falls_through_until_gtfo(self):
        body = "x\nWTF?\nOMG 1\nVISIBLE \"one\"\nOMG 2\nVISIBLE \"two\"\nGTFO\nOIC\n"
        self.assertEqual(run(body, "I HAS A x ITZ 1\n"), ["one", "two"])

    def test_loop_with_condition(self):
        body = "IM IN YR l UPPIN YR i TIL BOTH SAEM i AN 3\nVISIBLE i\nIM OUTTA YR l\n"
        self.assertEqual(run(body, "I HAS A i ITZ 0\n"), ["0", "1", "2"])

    def test_loop_break(self):
        body = ("IM IN YR l UPPIN YR i TIL BOTH SAEM i AN 10\n"
                "BOTH SAEM i AN 2\nO RLY?\nYA RLY\nGTFO\nOIC\nVISIBLE i\nIM OUTTA YR l\n")
        self.assertEqual(run(body, "I HAS A i ITZ 0\n"), ["0", "1"])

    # --- functions ---
    ADD = "HOW IZ I add YR a AN YR b\nFOUND YR SUM OF a AN b\nIF U SAY SO\n"

    def test_function_call_returns_value(self):
        self.assertEqual(run("VISIBLE I IZ add YR 2 AN YR 3 MKAY\n", functions=self.ADD), ["5"])

    def test_function_without_return_gives_noob(self):
        fn = "HOW IZ I quiet\nGTFO\nIF U SAY SO\n"
        self.assertEqual(run("VISIBLE I IZ quiet MKAY\n", functions=fn), ["NOOB"])


if __name__ == "__main__":
    unittest.main()
