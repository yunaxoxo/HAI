"""Regression tests for the LOLCODE parser (token list -> AST)."""
import unittest

from lexer import tokenize
from parser import (ArithExpr, Assignment, Break, CompareExpr, Concatenation, Conditional, Declaration,
                    FuncCall, FuncDef, InfiniteBool, Literal, Loop, PrintStmt, Program, Switch,
                    VariableSection, VarRef, parse)


def program(body, wazzup=""):
    decls = f"WAZZUP\n{wazzup}BUHBYE\n" if wazzup else ""
    return parse(tokenize(f"HAI\n{decls}{body}KTHXBYE\n"))


class ParserTests(unittest.TestCase):
    def assertRejects(self, source, fragment=""):
        with self.assertRaises(SyntaxError) as ctx:
            parse(tokenize(source))
        self.assertIn(fragment, str(ctx.exception))

    # --- program structure ---
    def test_minimal_program(self):
        self.assertEqual(program(""), Program(body=[], functions=[]))

    def test_requires_hai_and_kthxbye(self):
        self.assertRejects("VISIBLE 1\n", "Expected 'HAI'")
        self.assertRejects("HAI\nVISIBLE 1\n", "Expected 'KTHXBYE'")

    def test_functions_are_collected_outside_hai(self):
        tree = parse(tokenize("HOW IZ I f YR a\nFOUND YR a\nIF U SAY SO\nHAI\nKTHXBYE\n"))
        self.assertEqual([f.name for f in tree.functions], ["f"])
        self.assertIsInstance(tree.functions[0], FuncDef)
        self.assertEqual(tree.functions[0].params, ["a"])

    # --- variables (#13) ---
    def test_declarations_inside_wazzup(self):
        tree = program("x R 4\n", "I HAS A x ITZ 3\nI HAS A y\n")
        section, assign = tree.body
        self.assertIsInstance(section, VariableSection)
        self.assertEqual(section.declarations,
                         [Declaration("x", Literal("NUMBR", 3)), Declaration("y", None)])
        self.assertEqual(assign, Assignment("x", Literal("NUMBR", 4)))

    def test_declaration_outside_wazzup_is_rejected(self):
        self.assertRejects("HAI\nI HAS A x\nKTHXBYE\n", "WAZZUP")

    # --- literals ---
    def test_literal_kinds(self):
        tree = program('VISIBLE 7 + 2.5 + "hi" + WIN + FAIL + -3\n')
        kinds = [(v.kind, v.value) for v in tree.body[0].values]
        self.assertEqual(kinds, [("NUMBR", 7), ("NUMBAR", 2.5), ("YARN", "hi"),
                                 ("TROOF", True), ("TROOF", False), ("NUMBR", -3)])

    # --- VISIBLE (#14) ---
    def test_visible_operands_need_plus(self):
        tree = program('VISIBLE "a" + x\n', "I HAS A x\n")
        self.assertEqual(tree.body[1].values, [Literal("YARN", "a"), VarRef("x")])
        self.assertRejects('HAI\nVISIBLE "a" "b"\nKTHXBYE\n', "Expected '+'")
        self.assertRejects("HAI\nVISIBLE 1 +\nKTHXBYE\n", "Expected value")

    def test_visible_bang_suppresses_newline(self):
        self.assertTrue(program('VISIBLE "a"!\n').body[0].suppress_newline)
        self.assertFalse(program('VISIBLE "a"\n').body[0].suppress_newline)

    # --- expressions ---
    def test_nested_prefix_arithmetic(self):
        expr = program("VISIBLE SUM OF 1 AN PRODUKT OF 2 AN 3\n").body[0].values[0]
        self.assertEqual(expr, ArithExpr("SUM_OF", Literal("NUMBR", 1),
                                         ArithExpr("PRODUKT_OF", Literal("NUMBR", 2), Literal("NUMBR", 3))))

    def test_smoosh_requires_mkay_and_concatenates(self):
        expr = program('VISIBLE SMOOSH "a" AN "b" AN "c" MKAY\n').body[0].values[0]
        self.assertIsInstance(expr, Concatenation)
        self.assertEqual(len(expr.values), 3)

    # --- infinite-arity booleans (#15) ---
    def test_all_of_any_of_need_mkay(self):
        expr = program("VISIBLE ALL OF WIN AN FAIL MKAY\n").body[0].values[0]
        self.assertEqual(expr, InfiniteBool("ALL_OF", [Literal("TROOF", True), Literal("TROOF", False)]))
        self.assertRejects("HAI\nVISIBLE ALL OF WIN AN WIN\nKTHXBYE\n", "MKAY")

    def test_all_of_any_of_cannot_nest(self):
        self.assertRejects("HAI\nVISIBLE ALL OF ANY OF WIN AN WIN MKAY AN WIN MKAY\nKTHXBYE\n", "nested")

    # --- functions & loops ---
    def test_function_call_arguments(self):
        call = program("VISIBLE I IZ f YR 1 AN YR 2 MKAY\n").body[0].values[0]
        self.assertEqual(call, FuncCall("f", [Literal("NUMBR", 1), Literal("NUMBR", 2)]))

    def test_function_call_mkay_is_optional(self):
        call = program("VISIBLE I IZ f YR 1\n").body[0].values[0]
        self.assertEqual(call, FuncCall("f", [Literal("NUMBR", 1)]))

    def test_loop_node(self):
        tree = program("IM IN YR l UPPIN YR i TIL BOTH SAEM i AN 3\nVISIBLE i\nIM OUTTA YR l\n",
                       "I HAS A i ITZ 0\n")
        loop = tree.body[1]
        self.assertIsInstance(loop, Loop)
        self.assertEqual(loop.label, "l")
        self.assertIsInstance(loop.body[0], PrintStmt)

    # --- control flow: MEBBE, switch, nesting, comma soft breaks ---
    def test_conditional_with_mebbe_and_else(self):
        cond = program('BOTH SAEM 1 AN 1\nO RLY?\nYA RLY\nVISIBLE "a"\nMEBBE BOTH SAEM 1 AN 2\nVISIBLE "b"\n'
                       'NO WAI\nVISIBLE "c"\nOIC\n').body[0]
        self.assertIsInstance(cond, Conditional)
        self.assertEqual(len(cond.body), 1)
        self.assertEqual(len(cond.elseifs), 1)
        self.assertIsInstance(cond.elseifs[0]["condition"], CompareExpr)
        self.assertEqual(len(cond.else_body), 1)

    def test_switch_cases_break_and_default(self):
        switch = program('WTF?\nOMG 1\nVISIBLE "a"\nGTFO\nOMG "x"\nVISIBLE "b"\nOMGWTF\nVISIBLE "d"\nOIC\n').body[0]
        self.assertIsInstance(switch, Switch)
        self.assertEqual([c["value"] for c in switch.cases], [Literal("NUMBR", 1), Literal("YARN", "x")])
        self.assertIsInstance(switch.cases[0]["body"][-1], Break)
        self.assertEqual(len(switch.default), 1)

    def test_nested_switch_loops_and_conditional(self):
        tree = program(
            "WTF?\nOMG 1\nIM IN YR a UPPIN YR i TIL BOTH SAEM i AN 2\nIM IN YR b UPPIN YR j TIL BOTH SAEM j AN 2\n"
            "BOTH SAEM i AN j\nO RLY?\nYA RLY\nVISIBLE i\nOIC\nIM OUTTA YR b\nIM OUTTA YR a\nGTFO\nOIC\n",
            "I HAS A i ITZ 0\nI HAS A j ITZ 0\n")
        outer = tree.body[1].cases[0]["body"][0]
        self.assertIsInstance(outer, Loop)
        self.assertIsInstance(outer.body[0], Loop)
        self.assertIsInstance(outer.body[0].body[0], Conditional)

    def test_comma_is_a_soft_statement_break(self):
        self.assertEqual(program('VISIBLE "a", VISIBLE "b"\n').body,
                         program('VISIBLE "a"\nVISIBLE "b"\n').body)

    def test_unclosed_blocks_are_rejected(self):
        for body in ("BOTH SAEM 1 AN 1\nO RLY?\nYA RLY\nVISIBLE 1\n", "WTF?\nOMG 1\nVISIBLE 1\n",
                     "IM IN YR l UPPIN YR i TIL BOTH SAEM i AN 1\nVISIBLE i\n"):
            with self.subTest(body=body), self.assertRaises(SyntaxError):
                parse(tokenize(f"HAI\nWAZZUP\nI HAS A i ITZ 0\nBUHBYE\n{body}KTHXBYE\n"))

    # --- comments & line continuation ---
    def test_comments_are_ignored(self):
        source = "HAI\nBTW one\nOBTW\nmany\nlines\nTLDR\nVISIBLE 1 BTW tail\nKTHXBYE\n"
        self.assertEqual(len(parse(tokenize(source)).body), 1)

    def test_line_continuation(self):
        tree = program("VISIBLE 1 +...\n 2\n")
        self.assertEqual(len(tree.body[0].values), 2)

    # --- YARN escapes (#20) ---
    def test_yarn_escapes_are_decoded_in_literals(self):
        value = program('VISIBLE "a:)b:>c:od:"e::f"\n').body[0].values[0].value
        self.assertEqual(value, 'a\nb\tc\x07d"e:f')


if __name__ == "__main__":
    unittest.main()
