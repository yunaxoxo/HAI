# HAI interface design notes

This is a practical development-tool UI, not a visual dashboard or marketing page. The interface should communicate what the program does, and what the compiler found, with the fewest visual distractions.

## Layout

- The code buffer is the primary surface and occupies the full left column on desktop.
- AST, tokens and symbols share one inspector. Output and diagnostics share a console below it.
- Mobile uses Code / Explore / Output rather than shrinking all three panels into tiny cards. The mobile command bar uses two purposeful rows: HAI + Examples + file actions, then the labeled compiler actions; AST and console remain separate screens.
- There is no fictional file tree: HAI works with one program at a time.

## Visual system

- Use mostly neutral graphite. Reserve color for actual syntax roles, errors and successes.
- Panels are separated by quiet one-pixel lines rather than nested boxes and shadows.
- Toolbars use plain text actions with no hover boxes. `Run` is the only consistently filled action.
- A single Examples menu loads samples directly; do not introduce redundant Select + Load controls.
- Hover is a subtle text or background adjustment, never a lift, glow or animated transform.
- Selected AST rows have a flat low-contrast fill; source ranges still receive a clear editor highlight.
- The prompt for `GIMMEH` stays inside the console as one compact input row on desktop (stacked on small screens).
- The minimal startup view stays readable for about 1.65 seconds, then reveals **Launch editor** on first arrival. Activation fades into the initialized editor. Refreshes in the same browser tab skip the extra click when session storage is available. Reduced-motion settings shorten the hold and eliminate the fade. A retry fallback appears if JavaScript fails to initialize.

## Icon and brand system

- The browser favicon and home-screen icon are a custom H/dot monogram in the same neutral palette as the editor. Do not substitute a generic code bracket/logo.
- Use consistent 15px Lucide-style line glyphs on the five primary toolbar actions, with the same stroke weight and baseline. Desktop keeps text labels for every action. On narrow screens, only the universally familiar Open and Save file commands become icon-only with accessible names, tooltips and 44px tap targets. Tokenize, Analyze and Run always retain visible text.
- Lucide icon geometry is embedded inline in HTML to work offline. Attribution is maintained in `frontend/icons/LICENSE.md`.
- The tree inspector, footer, dialogs, and tabs remain text-led: no decorative icon badges, pill backgrounds, or multicolor icons.
- The opening remains a single wordmark, low-contrast subtitle and 1px progress line, followed by one understated **Launch editor** action. No extra motion beyond the line and brief fade.

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


## Opening the editor

On first arrival in a browser tab, HAI displays its quiet 1.65-second wordmark and loading line, then a single **Launch editor** button. The editor is initialized behind the welcome screen but remains inaccessible until the button is activated. The entry is remembered for the current tab session so refreshes return directly to the workbench after startup. Reduced-motion preferences shorten the loading phase. No extra routes or dependencies are introduced. If storage is unavailable, HAI simply shows the launch button again after reload.
