OBTW
    File Path: core_regression/core_18_redeclare_negative.lol
    Category: Core Regression
    Owner: Jericko — Interpreter (interpreter.py)
    Related GitHub Issue: Not specified (declaring a variable twice)
    Stdin Inputs: None
    ------------------------------------------------------------------------
    WHAT SHOULD HAPPEN:
    Expected Error: RuntimeError: Variable 'dup' is already declared.
    ------------------------------------------------------------------------
    IF IT DOES NOT HAPPEN — WHAT TO CHECK:
    Check the Declaration branch of Interpreter.execute().
TLDR
HAI
    WAZZUP
        I HAS A dup ITZ 1
        I HAS A dup ITZ 2
    BUHBYE
    VISIBLE dup
KTHXBYE
