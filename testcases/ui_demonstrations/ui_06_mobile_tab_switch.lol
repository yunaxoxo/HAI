OBTW
    File Path: ui_demonstrations/ui_06_mobile_tab_switch.lol
    Category: UI Demonstrations
    Owner: Gab — UI / Workbench (frontend/app.js)
    Related GitHub Issue: Issue #18 (Multiple open editor tabs)
    Stdin Inputs: None
    ------------------------------------------------------------------------
    WHAT SHOULD HAPPEN:
    1) Console Output: Tab B active: 99
    2) Opening alongside ui_01_highlighting.lol creates separate tabs.
    3) Switching tabs preserves independent buffers, dirty badges, AST, and console outputs.
    ------------------------------------------------------------------------
    IF IT DOES NOT HAPPEN — WHAT TO CHECK:
    Check state.documents, state.activeDocId, and tab bar rendering in frontend/app.js.
TLDR
HAI
    WAZZUP
        I HAS A tab_value ITZ 99 BTW Tab B state variable
    BUHBYE
    VISIBLE "Tab B active: " + tab_value BTW Output Tab B message
KTHXBYE

