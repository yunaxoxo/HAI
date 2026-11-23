OBTW
    File Path: ui_demonstrations/ui_03_error_diagnostic.lol
    Category: UI Demonstrations
    Owner: Gab — UI / Workbench & Desmond — Parser (parser.py)
    Related GitHub Issues: Issue #17 (AST views) & Issue #19 (Mobile usability)
    Stdin Inputs: None
    ------------------------------------------------------------------------
    WHAT SHOULD HAPPEN:
    1) Expected Error: SyntaxError on line 3
    2) Problems panel diagnostic entry appears and gutter error marker highlights line 3.
    3) Error banner remains visible even on <=440px screens.
    ------------------------------------------------------------------------
    IF IT DOES NOT HAPPEN — WHAT TO CHECK:
    Check renderDiagnostics(), gutter markers, and @media (max-width: 440px) rules
    in frontend/app.js and frontend/style.css.
TLDR
HAI
    VISIBLE "Before syntax error" BTW Executed statement
    VISIBLE SUM OF 5 BTW Syntax error: missing 'AN' and second operand on line 3
KTHXBYE

