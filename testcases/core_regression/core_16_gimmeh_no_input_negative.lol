OBTW
    File Path: core_regression/core_16_gimmeh_no_input_negative.lol
    Category: Core Regression
    Owner: Jericko — Interpreter (interpreter.py)
    Related GitHub Issue: Not specified (GIMMEH at end of input)
    Stdin Inputs: None
    ------------------------------------------------------------------------
    WHAT SHOULD HAPPEN:
    Expected Error: RuntimeError: No input left for GIMMEH answer. (run with empty stdin; no Python traceback)
    ------------------------------------------------------------------------
    IF IT DOES NOT HAPPEN — WHAT TO CHECK:
    Check the InputStmt branch of Interpreter.execute() converts EOFError to RuntimeError.
TLDR
HAI
    WAZZUP
        I HAS A answer
    BUHBYE
    GIMMEH answer
    VISIBLE answer
KTHXBYE
