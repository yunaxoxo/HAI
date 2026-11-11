# HAI interface design notes

This is a practical development-tool UI, not a visual dashboard or marketing page. The interface should communicate what the program does, and what the compiler found, with the fewest visual distractions.

## Layout

- The code buffer is the primary surface and occupies the full left column on desktop.
- AST, tokens and symbols share one inspector. Output and diagnostics share a console below it.
- Mobile uses Code / Explore / Output rather than shrinking all three panels into tiny cards.
- There is no fictional file tree: HAI works with one program at a time.

## Visual system

- Use mostly neutral graphite. Reserve color for actual syntax roles, errors and successes.
- Panels are separated by quiet one-pixel lines rather than nested boxes and shadows.
- Toolbars use plain text actions with no hover boxes. `Run` is the only consistently filled action.
- A single Examples menu loads samples directly; do not introduce redundant Select + Load controls.
- Hover is a subtle text or background adjustment, never a lift, glow or animated transform.
- Selected AST rows have a flat low-contrast fill; source ranges still receive a clear editor highlight.
- The prompt for `GIMMEH` stays inside the console as one compact input row on desktop (stacked on small screens).
- There is no startup delay or decorative loading animation. A minimal fallback remains if JavaScript cannot initialize.

## Interaction contract

Keep these functional when editing frontend styles or markup:

- `?` / `Shift + /` opens keyboard help outside normal text entry, as does `Cmd/Ctrl + /`.
- `Cmd/Ctrl + Enter` runs; `Cmd/Ctrl + O` opens; `Cmd/Ctrl + S` downloads.
- AST selections map to source, and source selections map back to AST nodes.
- `GIMMEH` input must accept Enter or Send; preset input is a separate optional workflow.
- File replacement and clearing preset input ask for confirmation as before.
- Accessible focus indicators and readable contrast take priority over aesthetic subtlety.

## References

Inspiration comes from the content-first organization of x86-64 Playground and restrained editor controls such as Zed. Do not copy their brand assets or exact layout. They are design references, not dependencies.
