# Release checklist

Before merging changes into the production branch:

- [ ] Run `python3 -B -m unittest discover -q`.
- [ ] Check `node --check frontend/app.js` if Node.js is available.
- [ ] Review the diff for credentials, private materials, generated files, and unrelated edits.
- [ ] Keep CodeMirror and icon attribution notices intact.
- [ ] Verify the Vercel Preview uses the intended Git commit.
- [ ] Verify favicon routes return images, not HTML, and the icon appears in a fresh browser tab.
- [ ] Check the editor, AST, keyboard shortcuts, `GIMMEH`, and mobile views.
- [ ] Confirm runtime execution safeguards before making the interpreter publicly accessible.
- [ ] Obtain maintainers' approval for a project-wide license, if the project will be open source.

The Vercel runner currently evaluates programs in-process without the local runner's hard timeout. This remains a release safety concern, not a documentation-only issue.
