OBTW
    File Path: core_regression/core_17_it_only_expression_statements.lol
    Category: Core Regression
    Owner: Jericko — Interpreter (interpreter.py)
    Related GitHub Issue: Spec p.5 (expression statements store into IT)
    Stdin Inputs: None
    ------------------------------------------------------------------------
    WHAT SHOULD HAPPEN:
    Console Output: x, 9, 2 (IT stays 2 from SUM OF 1 AN 1; VISIBLE and assignment do not change it)
    ------------------------------------------------------------------------
    IF IT DOES NOT HAPPEN — WHAT TO CHECK:
    Check Interpreter.quietly() is used for VISIBLE, assignment, declaration, loop and case operands.
TLDR
HAI
    WAZZUP
        I HAS A n ITZ 1
    BUHBYE
    SUM OF 1 AN 1
    n R 9
    VISIBLE "x"
    VISIBLE n
    VISIBLE IT
KTHXBYE
