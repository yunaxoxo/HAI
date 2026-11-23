OBTW
    File Path: extra_credit/bonus_08_yarn_escapes.lol
    Category: Extra Credit
    Owner: Zo — Lexer (lexer.py) & Desmond — Interpreter (interpreter.py)
    Related GitHub Issue: Issue #20 (YARN special escapes)
    Stdin Inputs: None
    ------------------------------------------------------------------------
    WHAT SHOULD HAPPEN:
    Console Output:
        Line 1
        Line 2	Tabbed: "Quoted"
    ------------------------------------------------------------------------
    IF IT DOES NOT HAPPEN — WHAT TO CHECK:
    If LexicalError occurs at :" or escapes print literally, check YARN scanning in
    lexer.py and escape decoding in parser.py / interpreter.py.
TLDR
HAI
    VISIBLE "Line 1:)Line 2:>Tabbed:: :"Quoted:":o" BTW Escapes: :) newline, :> tab, :: colon, :" quote, :o bell
KTHXBYE

