OBTW
    File Path: core_regression/core_05_undeclared_input_negative.lol
    Category: Core Regression
    Owner: Jericko — Interpreter (interpreter.py)
    Related GitHub Issue: Issue #12 (Enforce NOOB cast & GIMMEH checks)
    Stdin Inputs: Alice
    ------------------------------------------------------------------------
    WHAT SHOULD HAPPEN:
    Expected Error: RuntimeError: Undefined variable: undeclared_name
    ------------------------------------------------------------------------
    IF IT DOES NOT HAPPEN — WHAT TO CHECK:
    Check InputStmt execution in interpreter.py for variable existence check.
TLDR
HAI
    GIMMEH undeclared_name
    VISIBLE undeclared_name
KTHXBYE

