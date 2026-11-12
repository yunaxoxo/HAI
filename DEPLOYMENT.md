# Deployment

HAI can run locally using Python's standard library or on Vercel through the Flask adapter. The two environments have different execution safeguards.

## Local development

From the repository root:

```bash
python3 -B -m unittest discover -q
python3 -B app.py
```

Visit `http://127.0.0.1:8000`. No frontend build or npm install is needed. If available, `node --check frontend/app.js` provides an extra JavaScript syntax check.

## Vercel and GitHub

1. Connect the GitHub repository to your existing Vercel project (or import it through [Vercel](https://vercel.com/new)).
2. Keep the Root Directory at the repository root. The project uses `vercel.json`, `requirements.txt`, and `api/index.py`.
3. Configure `main` (or the team's intended release branch) as the Production branch.
4. Push changes to a feature branch and inspect the Git-backed **Preview** deployment.
5. Merge only after testing and review. A configured Git integration should then deploy the Production branch.

From a linked local directory, `vercel deploy` creates a Preview and `vercel deploy --prod` explicitly targets Production. Avoid deploying a test branch to Production.

## Verify a deployment

Check that the deployment uses the intended **Git commit** and that the site can:

- Open **Launch editor**, load examples, tokenize, analyze, and run LOLCODE.
- Navigate between AST nodes and source positions.
- Submit `GIMMEH` input and use keyboard help (`?`).
- Display a usable layout on mobile.
- Load `/app.js`, `/style.css`, the bundled `/vendor/` assets, and `/favicon.ico`, `/favicon.svg`, `/favicon-32x32.png`, `/apple-touch-icon.png` with HTTP 200 and the correct content types.

If an icon looks blank, open the asset URL directly and inspect DevTools → Network; browsers can cache favicons across normal refreshes. Verify the favicon files are tracked in Git and that Vercel is deploying the correct commit.

## Runtime security

**Do not assume Vercel provides the same code-execution safety as local development.** Locally, `app.py` runs the interpreter in a subprocess with a five-second timeout. The Flask adapter executes it in-process, without an equivalent per-program deadline or sandbox. Evaluate resource limits, input limits, abuse protections, and deployment access controls before exposing public execution.

## Troubleshooting

| Issue | Check |
| --- | --- |
| Preview differs from Production | Source, Git branch, commit, and environment in Vercel Deployments |
| Missing CSS, editor, or icons | File paths, HTTP status, MIME type, and Flask/static routes |
| API execution errors | Browser Network tab and Vercel Function logs |
| New UI not visible | Correct deployment URL and browser cache; try a private tab |

See [Architecture](docs/ARCHITECTURE.md) for endpoint and runtime details.
