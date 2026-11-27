OBTW
    File Path: core_regression/core_19_nested_call_mkay.lol
    Category: Core Regression
    Owner: Jericko — Interpreter (interpreter.py)
    Related GitHub Issue: Spec p.7 (calls end with MKAY)
    Stdin Inputs: None
    ------------------------------------------------------------------------
    WHAT SHOULD HAPPEN:
    Console Output: 9 (a nested call used as a non-final argument needs its own MKAY)
    ------------------------------------------------------------------------
    IF IT DOES NOT HAPPEN — WHAT TO CHECK:
    Check Parser.parse_function_call() argument parsing and MKAY handling.
TLDR
HOW IZ I add YR a AN YR b
    FOUND YR SUM OF a AN b
IF U SAY SO

HOW IZ I twice YR a
    FOUND YR PRODUKT OF a AN 2
IF U SAY SO

HAI
    WAZZUP
    BUHBYE
    VISIBLE I IZ add YR I IZ twice YR 4 MKAY AN YR 1 MKAY
KTHXBYE
