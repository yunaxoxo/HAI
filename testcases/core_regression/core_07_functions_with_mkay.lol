OBTW
    File Path: core_regression/core_07_functions_with_mkay.lol
    Category: Core Regression
    Owner: Jericko — Interpreter & Desmond — Parser
    Related GitHub Issues: Issue #9 & Issue #15
    Stdin Inputs: 5, 10, world
    ------------------------------------------------------------------------
    WHAT SHOULD HAPPEN:
    Console Output: 15, Hello, world, NOOB, 7
    ------------------------------------------------------------------------
    IF IT DOES NOT HAPPEN — WHAT TO CHECK:
    Check Parser.parse_function_call() in parser.py for optional MKAY support.
TLDR
HOW IZ I addNum YR x AN YR y
    FOUND YR SUM OF x AN y
IF U SAY SO

HOW IZ I printName YR person
    VISIBLE "Hello, " + person
    GTFO
IF U SAY SO

HOW IZ I printNum YR x
    FOUND YR x
IF U SAY SO

HAI
    WAZZUP
        I HAS A name
        I HAS A num1
        I HAS A num2
    BUHBYE
    GIMMEH num1
    GIMMEH num2
    I IZ addNum YR num1 AN YR num2 MKAY
    VISIBLE IT
    GIMMEH name
    I IZ printName YR name MKAY
    VISIBLE IT
    I IZ printNum YR SUM OF num1 AN 2 MKAY
    VISIBLE IT
KTHXBYE

