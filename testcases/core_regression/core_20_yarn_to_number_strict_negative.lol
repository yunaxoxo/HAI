OBTW
    File Path: core_regression/core_20_yarn_to_number_strict_negative.lol
    Category: Core Regression
    Owner: Jericko — Interpreter (interpreter.py)
    Related GitHub Issue: Spec p.4-5 (a YARN is numeric only with digits, hyphen and period)
    Stdin Inputs: None
    ------------------------------------------------------------------------
    WHAT SHOULD HAPPEN:
    Console Output: 3 then Expected Error: RuntimeError: Cannot convert '1_000' to a number.
    ------------------------------------------------------------------------
    IF IT DOES NOT HAPPEN — WHAT TO CHECK:
    Check Interpreter.number() rejects underscores, exponents and a leading + in YARNs.
TLDR
HAI
    VISIBLE SUM OF "1" AN "2"
    VISIBLE SUM OF "1_000" AN 1
KTHXBYE
