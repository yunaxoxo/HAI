# Release checklist

Before merging changes into the production branch:

- [ ] Run `python3 -B -m unittest discover -q`.
- [ ] Run `node --check frontend/app.js` if Node.js is available.
- [ ] Verify every README/documentation link points to an existing file or section.
- [ ] Review staged changes for secrets, private notes, generated artifacts, and unrelated files.
- [ ] Keep CodeMirror and icon licenses intact.
- [ ] Verify the Preview comes from the intended Git commit.
- [ ] Test editor, AST, Run, `GIMMEH`, shortcuts, favicon, and desktop/mobile layouts.
- [ ] Review serverless execution safeguards before allowing unrestricted public code execution.
- [ ] Confirm the team's decision about a project-wide software license.

See [Deployment](../DEPLOYMENT.md) for hosting and security details.
