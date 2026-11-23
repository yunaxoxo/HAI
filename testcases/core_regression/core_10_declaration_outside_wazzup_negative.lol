OBTW
    File Path: core_regression/core_10_declaration_outside_wazzup_negative.lol
    Category: Core Regression
    Owner: Desmond — Parser (parser.py)
    Related GitHub Issue: Issue #13 (Require WAZZUP-only declarations)
    Stdin Inputs: None
    ------------------------------------------------------------------------
    WHAT SHOULD HAPPEN:
    Expected Error: SyntaxError on line 5 at token "I_HAS_A"
    ------------------------------------------------------------------------
    IF IT DOES NOT HAPPEN — WHAT TO CHECK:
    Check Parser.parse_statement() in parser.py.
TLDR
HAI
    WAZZUP
        I HAS A valid ITZ 1
    BUHBYE
    I HAS A invalid ITZ 2
    VISIBLE invalid
KTHXBYE

