"""Specification-focused lexer with optional source spans for the workbench.

The parser-facing tokenize() contract remains (kind, raw_lexeme, line).
"""

import re
import os
import sys

TOKEN_SPECS = [
    ("NEWLINE",       r"\r\n|\r|\n"),
    ("SKIP",          r"[ \t]+"),

    # --- Separators & Delimiters ---
    ("PLUS",          r"\+"),             # VISIBLE operand separator
    ("COMMA",         r","),
    ("AN",            r"\bAN\b"),
    ("EXCLAMATION",   r"!"),              # Suppresses newline in VISIBLE

    # --- Core Structure & Variables ---
    ("HAI",           r"\bHAI\b"),
    ("KTHXBYE",       r"\bKTHXBYE\b"),
    ("WAZZUP",        r"\bWAZZUP\b"),
    ("BUHBYE",        r"\bBUHBYE\b"),
    ("I_HAS_A",       r"\bI HAS A\b"),
    ("ITZ",           r"\bITZ\b"),
    ("R",             r"\bR\b"),

    # --- Math Operations ---
    ("SUM_OF",        r"\bSUM OF\b"),
    ("DIFF_OF",       r"\bDIFF OF\b"),
    ("PRODUKT_OF",    r"\bPRODUKT OF\b"),
    ("QUOSHUNT_OF",   r"\bQUOSHUNT OF\b"),
    ("MOD_OF",        r"\bMOD OF\b"),
    ("BIGGR_OF",      r"\bBIGGR OF\b"),
    ("SMALLR_OF",     r"\bSMALLR OF\b"),

    # --- Boolean & Logic ---
    ("BOTH_OF",       r"\bBOTH OF\b"),
    ("EITHER_OF",     r"\bEITHER OF\b"),
    ("WON_OF",        r"\bWON OF\b"),
    ("NOT",           r"\bNOT\b"),
    ("ANY_OF",        r"\bANY OF\b"),
    ("ALL_OF",        r"\bALL OF\b"),

    # --- Comparison ---
    ("BOTH_SAEM",     r"\bBOTH SAEM\b"),
    ("DIFFRINT",      r"\bDIFFRINT\b"),

    # --- String Operations & Casting ---
    ("SMOOSH",        r"\bSMOOSH\b"),
    ("MAEK",          r"\bMAEK\b"),
    ("A",             r"\bA\b"),
    ("IS_NOW_A",      r"\bIS NOW A\b"),

    # --- I/O ---
    ("VISIBLE",       r"\bVISIBLE\b"),
    ("GIMMEH",        r"\bGIMMEH\b"),

    # --- Conditionals ---
    ("O_RLY?",        r"\bO RLY\?"),
    ("YA_RLY",        r"\bYA RLY\b"),
    ("MEBBE",         r"\bMEBBE\b"),
    ("NO_WAI",        r"\bNO WAI\b"),
    ("OIC",           r"\bOIC\b"),

    # --- Switch Statement ---
    ("WTF?",          r"\bWTF\?"),
    ("OMGWTF",        r"\bOMGWTF\b"),
    ("OMG",           r"\bOMG\b"),

    # --- Loops ---
    ("IM_IN_YR",      r"\bIM IN YR\b"),
    ("UPPIN",         r"\bUPPIN\b"),
    ("NERFIN",        r"\bNERFIN\b"),
    ("YR",            r"\bYR\b"),
    ("TIL",           r"\bTIL\b"),
    ("WILE",          r"\bWILE\b"),
    ("IM_OUTTA_YR",   r"\bIM OUTTA YR\b"),

    # --- Functions ---
    ("HOW_IZ_I",      r"\bHOW IZ I\b"),
    ("IF_U_SAY_SO",   r"\bIF U SAY SO\b"),
    ("GTFO",          r"\bGTFO\b"),
    ("FOUND_YR",      r"\bFOUND YR\b"),
    ("I_IZ",          r"\bI IZ\b"),

    # --- Special Tokens ---
    ("MKAY",          r"\bMKAY\b"),
    ("SRS",           r"\bSRS\b"),

    # --- Literals & Types ---
    ("NUMBAR",        r"-?[0-9]+\.[0-9]+"),
    ("NUMBR",         r"-?[0-9]+"),
    # Escapes are optional in the course PDF. Preserve literal text, including
    # ordinary colons; quote decoding/interpolation belongs to later stages.
    ("YARN",          r'"[^"\r\n]*"'),
    ("TROOF",         r"\b(WIN|FAIL)\b"),
    ("TYPE",          r"\b(NOOB|TROOF|NUMBR|NUMBAR|YARN|TYPE)\b"),
    ("NOOB",          r"\bNOOB\b"),

    # --- Identifiers ---
    ("IDENTIFIER",    r"[a-zA-Z][a-zA-Z0-9_]*"),
]

COMPILED_SPECS = [(name, re.compile(pattern)) for name, pattern in TOKEN_SPECS]
INPUT_FILE = "source.txt"
NEWLINE_RE = re.compile(r"\r\n|\r|\n")
BLOCK_OPEN_RE = re.compile(r"OBTW\b")
BLOCK_CLOSE_RE = re.compile(r"TLDR\b")
COMMENT_RE = re.compile(r"BTW\b")

class LexicalError(SyntaxError):
    """A SyntaxError with locations and completed tokens for the workbench."""

    def __init__(self, message, line, column, tokens, locations, offset, source_length):
        super().__init__(f"Line {line}, column {column}: {message}")
        self.line = line
        self.column = column
        self.end_line = line
        # At EOF there is no offending character to underline. Use an
        # empty span rather than inventing an offset beyond the source.
        width = 1 if offset < source_length else 0
        self.end_column = column + width
        self.start_offset = offset
        self.end_offset = offset + width
        self.tokens = list(tokens)
        self.token_locations = list(locations)


def tokenize(source):
    """Return the existing parser-compatible three-element token tuples."""
    tokens, _locations = tokenize_with_locations(source)
    return tokens


def tokenize_with_locations(source):
    """Return (tokens, source spans), aligned by token index.

    Positions are 1-based lines/columns and 0-based Python Unicode codepoint
    offsets, with exclusive end positions. CRLF/CR are represented as the
    canonical NEWLINE lexeme while spans preserve the original source offsets.
    The parser still receives only the original three-element token tuples.
    """
    tokens = []
    locations = []
    position = 0
    line_number = 1
    line_start = 0
    block_start = None

    def span(start, end, start_line, start_column, end_line, end_column):
        return {"line": start_line, "column": start_column,
                "end_line": end_line, "end_column": end_column,
                "start_offset": start, "end_offset": end}

    def fail(message, at=None):
        offset = position if at is None else at
        raise LexicalError(message, line_number, offset - line_start + 1,
                           tokens, locations, offset, len(source))

    while position < len(source):
        # Handle line endings first, including those inside discarded comments.
        ending = NEWLINE_RE.match(source, position)
        if ending:
            tokens.append(("NEWLINE", "\n", line_number))
            locations.append(span(position, ending.end(), line_number,
                                  position - line_start + 1, line_number + 1, 1))
            position = ending.end()
            line_number += 1
            line_start = position
            continue

        if block_start is not None:
            end = position
            while end < len(source) and source[end] not in "\r\n":
                end += 1
            content = source[position:end].strip(" \t")
            if re.match(r"TLDR\b", content):
                if not re.fullmatch(r"TLDR[ \t]*(?:BTW\b.*)?", content):
                    fail("TLDR must occupy its own line (an optional BTW comment is allowed).")
                block_start = None
            position = end
            continue

        if BLOCK_OPEN_RE.match(source, position):
            end = position
            while end < len(source) and source[end] not in "\r\n":
                end += 1
            content = source[position:end]
            if (source[line_start:position].strip(" \t") or
                    not re.fullmatch(r"OBTW[ \t]*(?:BTW\b.*)?", content)):
                fail("OBTW must occupy its own line (an optional BTW comment is allowed).")
            block_start = line_number
            position = end
            continue

        if BLOCK_CLOSE_RE.match(source, position):
            fail("TLDR has no matching OBTW.")

        if COMMENT_RE.match(source, position):
            while position < len(source) and source[position] not in "\r\n":
                position += 1
            continue

        for name, regex in COMPILED_SPECS:
            match = regex.match(source, position)
            if match:
                break
        else:
            if source[position] == '"':
                fail("Unterminated YARN; strings must end on the same physical line.")
            fail(f"Cannot read {source[position]!r}.")

        text = match.group()
        if name in ("NUMBR", "NUMBAR") and match.end() < len(source):
            following = source[match.end()]
            if following.isalnum() or following in "_.":
                fail("Invalid numeric literal or identifier beginning with a digit.")
        if name != "SKIP":
            tokens.append((name, text, line_number))
            locations.append(span(position, match.end(), line_number,
                                  position - line_start + 1, line_number,
                                  match.end() - line_start + 1))
        position = match.end()

    if block_start is not None:
        fail(f"Unterminated block comment opened on line {block_start}; expected TLDR.")
    return tokens, locations

def read_input(filepath):
    if not os.path.isfile(filepath):
        print(f"Error: '{filepath}' not found.")
        sys.exit(1)
    
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    source_text = read_input(INPUT_FILE)
    for token in tokenize(source_text):
        print(token)
