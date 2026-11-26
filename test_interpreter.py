"""Regression tests for the LOLCODE interpreter (execution semantics)."""
import unittest
from pathlib import Path

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

    def test_quoshunt_of_numbrs_is_integer_division(self):
        for expr, expected in [("4 AN 5", "0"), ("5 AN 2", "2"), ("-7 AN 2", "-3"), ("7 AN -2", "-3")]:
            with self.subTest(expr=expr):
                self.assertEqual(run(f"VISIBLE QUOSHUNT OF {expr}\n"), [expected])

    def test_quoshunt_with_a_numbar_is_float_division(self):
        self.assertEqual(run("VISIBLE QUOSHUNT OF 4.0 AN 5.0\nVISIBLE QUOSHUNT OF 7 AN 2.0\n"), ["0.8", "3.5"])

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

    def test_numbar_to_yarn_truncates_to_two_decimals(self):
        self.assertEqual(run("VISIBLE MAEK 3.14159 YARN\nVISIBLE 2.5\nVISIBLE 3.149\nVISIBLE 0.29\n"),
                         ["3.14", "2.5", "3.14", "0.29"])
        self.assertEqual(run("VISIBLE SUM OF 0.1 AN 0.2\nVISIBLE 4.0\n"), ["0.3", "4.0"])

    def test_numbar_display_ignores_binary_noise(self):
        self.assertEqual(run("VISIBLE DIFF OF 4 AN 3.14\nVISIBLE PRODUKT OF 0.57 AN 100\nVISIBLE 3.14159\n"),
                         ["0.86", "57.0", "3.14"])

    # --- NOOB / strict comparison / GIMMEH rules (#12) ---
    def test_noob_cannot_be_implicitly_numeric(self):
        for body in ("VISIBLE SUM OF u AN 1\n",
                     "IM IN YR l UPPIN YR u TIL BOTH SAEM u AN 2\nIM OUTTA YR l\n"):
            with self.subTest(body=body), self.assertRaisesRegex(RuntimeError, "NOOB to a number"):
                run(body, "I HAS A u\n")

    def test_noob_explicit_casts_succeed(self):
        body = "VISIBLE MAEK u NUMBR\nVISIBLE MAEK u NUMBAR\nVISIBLE MAEK u TROOF\nVISIBLE u\n"
        self.assertEqual(run(body, "I HAS A u\n"), ["0", "0.0", "FAIL", "NOOB"])

    def test_gimmeh_requires_a_declared_variable(self):
        with self.assertRaisesRegex(RuntimeError, "Undefined variable: ghost"):
            run("GIMMEH ghost\n", inputs=["x"])

    def test_comparisons_do_not_cast_types(self):
        for expr, expected in [("BOTH SAEM WIN AN 1", "FAIL"), ("DIFFRINT 1 AN 1.0", "WIN"),
                               ("BOTH SAEM 1 AN 1.0", "FAIL"), ('BOTH SAEM "5" AN 5', "FAIL"),
                               ("BOTH SAEM 1.5 AN 1.5", "WIN"), ('BOTH SAEM "a" AN "a"', "WIN"),
                               ("BOTH SAEM WIN AN WIN", "WIN")]:
            with self.subTest(expr=expr):
                self.assertEqual(run(f"VISIBLE {expr}\n"), [expected])

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

    def test_switch_falls_through_until_gtfo(self):
        body = 'x\nWTF?\nOMG 1\nVISIBLE "one"\nOMG 2\nVISIBLE "two"\nGTFO\nOMG 3\nVISIBLE "three"\nOIC\n'
        self.assertEqual(run(body, "I HAS A x ITZ 1\n"), ["one", "two"])
        self.assertEqual(run(body, "I HAS A x ITZ 3\n"), ["three"])

    def test_switch_last_case_does_not_run_the_default(self):
        body = 'x\nWTF?\nOMG 0\nVISIBLE "bye"\nOMGWTF\nVISIBLE "invalid"\nOIC\n'
        self.assertEqual(run(body, "I HAS A x ITZ 0\n"), ["bye"])

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

    def test_gtfo_after_output_returns_noob_not_stale_it(self):
        fn = 'HOW IZ I shout\nVISIBLE "hey"\nGTFO\nIF U SAY SO\n'
        self.assertEqual(run("I IZ shout MKAY\nVISIBLE IT\n", functions=fn), ["hey", "NOOB"])

    def test_falling_off_function_end_returns_noob(self):
        fn = 'HOW IZ I shout\nVISIBLE "hey"\nIF U SAY SO\n'
        self.assertEqual(run("I IZ shout MKAY\nVISIBLE IT\n", functions=fn), ["hey", "NOOB"])

    def test_found_yr_sets_callers_it(self):
        self.assertEqual(run("I IZ add YR 2 AN YR 3 MKAY\nVISIBLE IT\n", functions=self.ADD), ["5"])


    # --- scope isolation (#11) ---
    def test_function_cannot_read_outer_variable(self):
        fn = "HOW IZ I peek\nFOUND YR g\nIF U SAY SO\n"
        with self.assertRaisesRegex(RuntimeError, "Undefined variable: g"):
            run("VISIBLE I IZ peek MKAY\n", "I HAS A g ITZ 1\n", functions=fn)

    def test_function_cannot_write_outer_variable(self):
        fn = "HOW IZ I poke\ng R 2\nFOUND YR g\nIF U SAY SO\n"
        out = run("I IZ poke MKAY\nVISIBLE g\n", "I HAS A g ITZ 1\n", functions=fn)
        self.assertEqual(out, ["1"])  # the function made its own g; the caller's is untouched

    def test_parameters_are_passed_by_value(self):
        fn = "HOW IZ I bump YR n\nn R SUM OF n AN 1\nFOUND YR n\nIF U SAY SO\n"
        out = run("VISIBLE I IZ bump YR x MKAY\nVISIBLE x\n", "I HAS A x ITZ 5\n", functions=fn)
        self.assertEqual(out, ["6", "5"])

    def test_control_flow_inside_function_sees_its_locals(self):
        fn = ("HOW IZ I count YR n\n"
              "BOTH SAEM n AN 1\nO RLY?\nYA RLY\nVISIBLE \"start\"\nOIC\n"
              "IM IN YR l UPPIN YR n TIL BOTH SAEM n AN 3\nVISIBLE n\nIM OUTTA YR l\n"
              "IF U SAY SO\n")
        self.assertEqual(run("I IZ count YR 1 MKAY\n", functions=fn), ["start", "1", "2"])


OFFICIAL = Path(__file__).with_name("project-testcases-fixed")


def run_file(name, inputs=()):
    """Run an official suite file and return what VISIBLE printed as one string."""
    out, queue = [], iter(inputs)
    Interpreter(input_func=lambda prompt="": next(queue),
                output_func=lambda text="", end="\n": out.append(f"{text}{end}")
                ).run_source((OFFICIAL / name).read_text())
    return "".join(out)


MENU = "1. Compute age\n2. Compute tip\n3. Compute square area\n0. Exit\nChoice: \n"


class OfficialSuiteTests(unittest.TestCase):
    """Exact output of the ten official test programs (project-testcases-fixed/)."""

    def test_01_variables(self):
        self.assertEqual(run_file("01_variables.lol"),
                         "declarations\nNOOB\n17\nseventeen\n17.0\nWIN\n30\n13\n12\n0\n30\n22\n")

    def test_02_gimmeh(self):
        self.assertEqual(run_file("02_gimmeh.lol", ["5", "10", "3"]), "22\n5\n7\n")

    def test_03_arith_numbr_and_numbar(self):
        self.assertEqual(run_file("03_arith.lol", ["4", "5"]),
                         "4+5 = 9\n4-5 = -1\n4*5 = 20\n4/5 = 0\n4%5 = 4\nmax(4,5) = 5\nmin(4,5) = 4\n41\n81\n1\n5\n8\n")
        self.assertEqual(run_file("03_arith.lol", ["4.0", "5.0"]),
                         "4.0+5.0 = 9.0\n4.0-5.0 = -1.0\n4.0*5.0 = 20.0\n4.0/5.0 = 0.8\n4.0%5.0 = 4.0\n"
                         "max(4.0,5.0) = 5.0\nmin(4.0,5.0) = 4.0\n41.0\n81.0\n1.0\n5.25\n8.25\n")

    def test_04_smoosh_assign(self):
        self.assertEqual(run_file("04_smoosh_assign.lol", ["foo", "bar"]),
                         "Hello! Please enter two strings:\nString 1: \nString 2: \n"
                         "foobar\nfoofoofoobarbar\nfoobar526151004End!\n10100\n10100.0\nFAIL\n")

    def test_05_bool(self):
        self.assertEqual(run_file("05_bool.lol"),
                         'x:WIN y:WIN\nWIN\nWIN\nFAIL\nFAIL\nWIN\nWIN\nWIN\nWIN\nx:FAIL y:WIN\nFAIL\nWIN\nWIN\nWIN\nFAIL\nWIN\nWIN\nFAIL\nx:FAIL y:FAIL\nFAIL\nFAIL\nFAIL\nWIN\nFAIL\nFAIL\nWIN\nFAIL\n')

    def test_06_comparison(self):
        self.assertEqual(run_file("06_comparison.lol", ["3", "3"]),
                         "Value 1: \nValue 2: \nWIN\nFAIL\nWIN\nWIN\nFAIL\nFAIL\n")
        self.assertEqual(run_file("06_comparison.lol", ["2", "3"]),
                         "Value 1: \nValue 2: \nFAIL\nWIN\nFAIL\nWIN\nWIN\nFAIL\n")

    def test_07_ifelse_with_mebbe(self):
        cases = [(["1", "20"], "Enter birth year: \n2002\n"), (["2", "50"], "Enter bill cost: \nTip: 5.0\n"),
                 (["3", "4"], "Enter width: \nSquare Area: 16\n"), (["0"], "Goodbye\n"),
                 (["9"], "Invalid Input!\nInvalid input is > 3.\n")]
        for inputs, tail in cases:
            with self.subTest(inputs=inputs):
                self.assertEqual(run_file("07_ifelse.lol", inputs), MENU + tail)

    def test_08_switch(self):
        cases = [(["1", "30"], "Enter birth year: \n1992\n"), (["2", "50"], "Enter bill cost: \nTip: 5.0\n"),
                 (["3", "4"], "Enter width: \nSquare Area: 16\n"), (["0"], "Goodbye\n"),
                 (["9"], "Invalid Input!\n")]
        for inputs, tail in cases:
            with self.subTest(inputs=inputs):
                self.assertEqual(run_file("08_switch.lol", inputs), MENU + tail)

    def test_09_loops(self):
        self.assertEqual(run_file("09_loops.lol", ["3"]), "Gimmeh a number: \n0\n1\n2\n3\n***\n4\n3\n2\n1\n")

    def test_10_functions(self):
        self.assertEqual(run_file("10_functions.lol", ["5", "10", "world"]), "15\nHello, world\nNOOB\n7\n")


class CoreRegressionTests(unittest.TestCase):
    """The core_regression demo cases as inline programs (the .lol files live outside this repo)."""

    def test_core_01_and_07_functions_gtfo_with_and_without_mkay(self):
        for call_end in ("", " MKAY"):
            body = (f"GIMMEH n1\\nGIMMEH n2\\nI IZ addNum YR n1 AN YR n2{call_end}\\nVISIBLE IT\\n"
                    f"GIMMEH w\\nI IZ printName YR w{call_end}\\nVISIBLE IT\\n"
                    f"I IZ printNum YR SUM OF n1 AN 2{call_end}\\nVISIBLE IT\\n").replace("\\n", "\n")
            fns = ("HOW IZ I addNum YR x AN YR y\nFOUND YR SUM OF x AN y\nIF U SAY SO\n"
                   'HOW IZ I printName YR p\nVISIBLE "Hello, " + p\nGTFO\nIF U SAY SO\n'
                   "HOW IZ I printNum YR x\nFOUND YR x\nIF U SAY SO\n")
            with self.subTest(call_end=call_end):
                self.assertEqual(run(body, "I HAS A n1\nI HAS A n2\nI HAS A w\n", ["5", "10", "world"], fns),
                                 ["15", "Hello, world", "NOOB", "7"])

    def test_core_02_integer_division(self):
        self.assertEqual(run("VISIBLE QUOSHUNT OF 4 AN 5\nVISIBLE QUOSHUNT OF 5 AN 2\n"
                             "VISIBLE QUOSHUNT OF -7 AN 2\nVISIBLE QUOSHUNT OF 4.0 AN 5.0\n"), ["0", "2", "-3", "0.8"])

    def test_core_03_no_implicit_return(self):
        fn = 'HOW IZ I sayHi\nVISIBLE "Hello, world"\nIF U SAY SO\n'
        self.assertEqual(run("I IZ sayHi MKAY\nVISIBLE IT\n", functions=fn), ["Hello, world", "NOOB"])

    def test_core_04_function_scope_negative(self):
        fn = "HOW IZ I leakSecret\nVISIBLE secret\nIF U SAY SO\n"
        with self.assertRaisesRegex(RuntimeError, "Undefined variable: secret"):
            run("I IZ leakSecret MKAY\n", "I HAS A secret ITZ 99\n", functions=fn)

    def test_core_05_undeclared_input_negative(self):
        with self.assertRaisesRegex(RuntimeError, "Undefined variable: undeclared_name"):
            run("GIMMEH undeclared_name\nVISIBLE undeclared_name\n", inputs=["Alice"])

    def test_core_06_noob_implicit_numeric_negative(self):
        with self.assertRaisesRegex(RuntimeError, "Cannot implicitly convert NOOB to a number."):
            run("VISIBLE SUM OF uninitialized AN 1\n", "I HAS A uninitialized\n")

    def test_core_08_comparison_strict_types(self):
        self.assertEqual(run('VISIBLE BOTH SAEM WIN AN 1\nVISIBLE DIFFRINT 1 AN 1.0\nVISIBLE BOTH SAEM "5" AN 5\n'),
                         ["FAIL", "WIN", "FAIL"])

    def test_core_09_numbar_yarn_truncation(self):
        self.assertEqual(run("VISIBLE MAEK pi A YARN\nVISIBLE MAEK half A YARN\n",
                             "I HAS A pi ITZ 3.14159\nI HAS A half ITZ 2.5\n"), ["3.14", "2.5"])

    def test_core_13_noob_explicit_cast(self):
        self.assertEqual(run("VISIBLE MAEK u A NUMBR\nVISIBLE MAEK u A NUMBAR\nVISIBLE MAEK u A TROOF\n",
                             "I HAS A u\n"), ["0", "0.0", "FAIL"])


class ExtraCreditTests(unittest.TestCase):
    """Working bonus features: MEBBE, nested control flow, VISIBLE !, comma soft breaks."""

    def test_mebbe_branch(self):
        body = ("BOTH SAEM score AN 100\nO RLY?\nYA RLY\nVISIBLE \"Perfect\"\nMEBBE BOTH SAEM score AN BIGGR OF score AN 80\n"
                "VISIBLE \"MEBBE branch\"\nNO WAI\nVISIBLE \"Keep trying\"\nOIC\n")
        self.assertEqual(run(body, "I HAS A score ITZ 85\n"), ["MEBBE branch"])
        self.assertEqual(run(body, "I HAS A score ITZ 100\n"), ["Perfect"])
        self.assertEqual(run(body, "I HAS A score ITZ 50\n"), ["Keep trying"])

    def test_nested_if(self):
        body = ("outer\nO RLY?\nYA RLY\ninner\nO RLY?\nYA RLY\nVISIBLE \"Inner true\"\nNO WAI\nVISIBLE \"Nested IF works\"\nOIC\n"
                "NO WAI\nVISIBLE \"Outer false\"\nOIC\n")
        self.assertEqual(run(body, "I HAS A outer ITZ WIN\nI HAS A inner ITZ FAIL\n"), ["Nested IF works"])

    def test_nested_switch(self):
        body = ("outer\nWTF?\nOMG 1\ninner\nWTF?\nOMG \"A\"\nVISIBLE \"Branch 1-A\"\nGTFO\n"
                "OMG \"B\"\nVISIBLE \"Nested SWITCH works\"\nGTFO\nOIC\nGTFO\nOMGWTF\nVISIBLE \"Default\"\nOIC\n")
        self.assertEqual(run(body, "I HAS A outer ITZ 1\nI HAS A inner ITZ \"B\"\n"), ["Nested SWITCH works"])

    def test_nested_loops(self):
        body = ("IM IN YR outer UPPIN YR i TIL BOTH SAEM i AN 2\nj R 0\nIM IN YR inner UPPIN YR j TIL BOTH SAEM j AN 2\n"
                'VISIBLE i + ":" + j\nIM OUTTA YR inner\nIM OUTTA YR outer\n')
        self.assertEqual(run(body, "I HAS A i ITZ 0\nI HAS A j ITZ 0\n"), ["0:0", "0:1", "1:0", "1:1"])

    def test_loop_with_conditional_inside(self):
        body = ("IM IN YR loop UPPIN YR idx TIL BOTH SAEM idx AN 2\nBOTH SAEM idx AN 0\nO RLY?\nYA RLY\nVISIBLE \"zero\"\n"
                "NO WAI\nVISIBLE \"one\"\nOIC\nIM OUTTA YR loop\n")
        self.assertEqual(run(body, "I HAS A idx ITZ 0\n"), ["zero", "one"])

    def test_loop_nerfin_and_wile(self):
        body = "IM IN YR l NERFIN YR n WILE DIFFRINT n AN 0\nVISIBLE n\nIM OUTTA YR l\n"
        self.assertEqual(run(body, "I HAS A n ITZ 3\n"), ["3", "2", "1"])

    def test_visible_bang_keeps_the_line_open(self):
        out = []
        Interpreter(output_func=lambda text="", end="\n": out.append(f"{text}{end}")).run_source(
            'HAI\nVISIBLE "Hello "!\nVISIBLE "world"\nKTHXBYE\n')
        self.assertEqual("".join(out), "Hello world\n")

    def test_comma_soft_break(self):
        self.assertEqual(run('VISIBLE "First", VISIBLE "Second"\n'), ["First", "Second"])


if __name__ == "__main__":
    unittest.main()
