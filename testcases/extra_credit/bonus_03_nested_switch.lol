OBTW
    File Path: extra_credit/bonus_03_nested_switch.lol
    Category: Extra Credit
    Owner: Desmond — Parser (parser.py) & Jericko — Interpreter (interpreter.py)
    Related GitHub Issue: Issue #22 (Expand automated regression test coverage)
    Stdin Inputs: None
    ------------------------------------------------------------------------
    WHAT SHOULD HAPPEN:
    Console Output: Nested SWITCH works
    ------------------------------------------------------------------------
    IF IT DOES NOT HAPPEN — WHAT TO CHECK:
    Check BreakSignal (GTFO) scoping in nested Switch execution in interpreter.py.
TLDR
HAI
    WAZZUP
        I HAS A outer ITZ 1
        I HAS A inner ITZ "B"
    BUHBYE
    outer
    WTF?
        OMG 1
            inner
            WTF?
                OMG "A"
                    VISIBLE "Branch 1-A"
                    GTFO
                OMG "B"
                    VISIBLE "Nested SWITCH works"
                    GTFO
            OIC
            GTFO
        OMGWTF
            VISIBLE "Default"
    OIC
KTHXBYE

