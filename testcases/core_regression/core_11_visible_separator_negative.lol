OBTW
    File Path: core_regression/core_11_visible_separator_negative.lol
    Category: Core Regression
    Owner: Desmond — Parser (parser.py)
    Related GitHub Issue: Issue #14 (Require + separator in VISIBLE)
    Stdin Inputs: None
    ------------------------------------------------------------------------
    WHAT SHOULD HAPPEN:
    Expected Error: SyntaxError on line 2 at token "b"
    ------------------------------------------------------------------------
    IF IT DOES NOT HAPPEN — WHAT TO CHECK:
    Check Parser.parse_print_list() in parser.py.
TLDR
HAI
    VISIBLE "a" "b"
KTHXBYE

