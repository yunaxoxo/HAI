OBTW
    File Path: extra_credit/bonus_06_visible_bang.lol
    Category: Extra Credit
    Owner: Desmond — Parser (parser.py) & Jericko — Interpreter (interpreter.py)
    Related GitHub Issue: Issue #22 (Expand automated regression test coverage)
    Stdin Inputs: None
    ------------------------------------------------------------------------
    WHAT SHOULD HAPPEN:
    Console Output: Hello world (single line without newline between strings)
    ------------------------------------------------------------------------
    IF IT DOES NOT HAPPEN — WHAT TO CHECK:
    Check self.match("EXCLAMATION") in Parser.parse_print() in parser.py.
TLDR
HAI
    VISIBLE "Hello "! BTW Trailing exclamation suppresses newline
    VISIBLE "world" BTW Output appended to same console line
KTHXBYE

