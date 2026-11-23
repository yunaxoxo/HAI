OBTW
    File Path: ui_demonstrations/ui_01_highlighting.lol
    Category: UI Demonstrations
    Owner: Gab — UI / Workbench (frontend/app.js) & Zo — Lexer (lexer.py)
    Related GitHub Issue: Issue #16 (Descriptive token classifications)
    Stdin Inputs: None
    ------------------------------------------------------------------------
    WHAT SHOULD HAPPEN:
    1) Console Output: HAI, CMSC 124! and 15
    2) Tokens table displays descriptive classifications ("Variable declaration keyword", etc.)
       with raw token kinds (I_HAS_A) as secondary metadata.
    3) Symbol Table updates to show count = 15 (NUMBR) and title = "HAI, CMSC 124!" (YARN).
    ------------------------------------------------------------------------
    IF IT DOES NOT HAPPEN — WHAT TO CHECK:
    Check tokenDescription() and renderTokens() in frontend/app.js and TOKEN_SPECS in lexer.py.
TLDR
HAI
    WAZZUP
        BTW Demonstrate keywords, literals, operators, and comments
        I HAS A count ITZ 10 BTW Integer declaration
        I HAS A title ITZ "HAI, CMSC 124!" BTW String declaration
    BUHBYE
    VISIBLE title BTW Output title variable
    count R SUM OF count AN 5 BTW Reassign count variable
    VISIBLE count BTW Output updated count
KTHXBYE

