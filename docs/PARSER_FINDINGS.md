# Findings for the parser and interpreter owners

Both issues were found while checking the lexer against the supplied course
programs. Neither was changed by the lexer/frontend work.

## 1. `VISIBLE` operands separated by `+` are rejected (parser)

- Affects: `03_arith`, `04_smoosh_assign`, `05_bool`, `07_ifelse`, `10_functions`.
- Example: `VISIBLE x + "+" + y` stops with `Unexpected token '+' (PLUS)`.
- Cause: the lexer now emits `PLUS` (the course PDF uses `+` between operands),
  but `parse_print` does not consume it.
- Evidence: with `PLUS` tokens filtered out, these five programs parse.
- Suggested fix: accept an optional `PLUS` between `VISIBLE` operands.
- Status: **open**, not fixed yet (confirmed bug, needs the parser owner).

## 2. A bare variable on its own line is rejected (parser)

- Affects: `08_switch` line 17 (`choice` before `WTF?`).
- Error: `Unexpected identifier 'choice' statement.`
- Expected: an expression statement that sets `IT`, which `WTF?` then reads.
- Suggested fix: allow a variable reference as a statement.
- Status: **open**, not fixed yet (confirmed for parsing; the runtime effect on `IT` was not tested).

## 3. `NOOB` is lexed as `TYPE` (contract note)

The parser consumes `TYPE` for cast targets, so the lexer keeps `NOOB` as
`TYPE`. Not a bug; changing it would need both sides to agree.

