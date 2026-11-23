OBTW
    File Path: core_regression/core_04_function_scope_negative.lol
    Category: Core Regression
    Owner: Jericko — Interpreter (interpreter.py)
    Related GitHub Issue: Issue #11 (Function scope isolation)
    Stdin Inputs: None
    ------------------------------------------------------------------------
    WHAT SHOULD HAPPEN:
    Expected Error: RuntimeError: Undefined variable: secret
    ------------------------------------------------------------------------
    IF IT DOES NOT HAPPEN — WHAT TO CHECK:
    Check Interpreter.get() and Interpreter.set() in interpreter.py.
TLDR
HOW IZ I leakSecret
    VISIBLE secret
IF U SAY SO

HAI
    WAZZUP
        I HAS A secret ITZ 99
    BUHBYE
    I IZ leakSecret MKAY
KTHXBYE

