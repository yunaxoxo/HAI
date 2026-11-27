OBTW
    File Path: core_regression/core_15_assign_undeclared_negative.lol
    Category: Core Regression
    Owner: Jericko — Interpreter (interpreter.py)
    Related GitHub Issue: Spec p.2 (all variables are declared in WAZZUP)
    Stdin Inputs: None
    ------------------------------------------------------------------------
    WHAT SHOULD HAPPEN:
    Expected Error: RuntimeError: Undefined variable: ghost
    ------------------------------------------------------------------------
    IF IT DOES NOT HAPPEN — WHAT TO CHECK:
    Check the Assignment branch of Interpreter.execute() calls get() before set().
TLDR
HAI
    WAZZUP
        I HAS A real ITZ 1
    BUHBYE
    ghost R 5
    VISIBLE ghost
KTHXBYE
