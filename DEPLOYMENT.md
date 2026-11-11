# Deploying HAI to Vercel

HAI is a plain HTML/CSS/JavaScript workbench powered by a Python interpreter. You do **not** need React, Vite, or a Node build step. Vercel runs the Flask adapter in `api/index.py` as a Python function; the local `app.py` server is still used for offline development.

## Before deploying

From the repository root, run:

```bash
python3 -B -m unittest discover -q
node --check frontend/app.js
python3 -B app.py
```

Visit `http://127.0.0.1:8000` and verify that Tokenize, Analyze, Run, the AST inspector, the **Shortcuts** reference, the sample selector, and `GIMMEH` input all work. The JavaScript syntax check requires Node, but running the local app does not.

Review `git status --short` and `git ls-files` before sharing a public repository. Do not commit private course PDFs, credentials, secrets, user data, build caches, or internal AI/developer handoffs. Only the code, tests, necessary license, and public documentation belong in the published repository.

## Option 1 — Deploy with GitHub (recommended)

1. Commit the public project files to your desired Git branch and push the branch to GitHub.
2. Sign in to [Vercel](https://vercel.com/new). Choose **Add New > Project**, then import the GitHub repository.
3. Set **Root Directory** to the repository root (the directory containing `vercel.json`, `requirements.txt`, `frontend/`, and `api/`).
4. Keep Vercel's default build settings for this Python project. If the framework is not detected, select **Other**. You should not specify an npm build command or JavaScript output directory.
5. Confirm `requirements.txt` and `api/index.py` are present. The included `vercel.json` routes requests to the Python entry point.
6. Select **Deploy** and open the deployment URL after its status is Ready. Vercel's Git integration normally creates preview deployments for nonproduction branches, and production deployments from the configured production branch.

Before making the link public, test the deployed application with a small program. On mobile, confirm that **Samples** opens the selector without crowding the editor, and that **Analyze** and **Run** take you to the correct views:

```lolcode
HAI
VISIBLE "HAI, WORLD!"
KTHXBYE
```

Press **Run**. Also try **Analyze** and **Tokenize**, and confirm selecting an AST node highlights its source location. Check the **Shortcuts** footer control, **Shift + /** (`?`), and Cmd/Ctrl + /, the source replacement dialog, the download filename dialog, and the styled sample menu. On a small screen, test a lexer error: the Problems view should open, and **Reveal in source** should take you back to the highlighted code.

## Option 2 — Vercel CLI

Install the CLI (Node.js required for the CLI, **not** for the HAI frontend):

```bash
npm install -g vercel
vercel login
cd path/to/your/lolcode-repository
vercel
```

Follow the prompts, choosing your own account/team and linking or creating a project. The first command deploys a **preview**. Inspect its URL and verify it works. Once ready to publish production:

```bash
vercel --prod
```

You can use `vercel dev` to exercise the platform's routing locally if the CLI and Python dependencies are installed. For everyday offline development, `python3 -B app.py` remains sufficient.

## What Vercel runs

- `/` serves the HTML workbench.
- `/style.css`, `/app.js`, and `/vendor/...` serve the bundled editor assets.
- `/api/tokenize`, `/api/analyze`, and `/api/run` accept JSON from the frontend.
- `requirements.txt` installs Flask for Vercel. The local Python server does not need Flask.
- On Vercel, Run uses the in-process `run_program_inline` adapter because it doesn't depend on a child process. Locally, `run_program` uses a child process with a five-second timeout.

## Troubleshooting

- **404 or blank page:** Check that the Vercel Root Directory is correct, and confirm `api/index.py` and `vercel.json` were committed. Inspect deployment logs.
- **Editor has no highlighting:** Check the browser's Network tab for successful requests to `/vendor/codemirror.js` and `/vendor/codemirror.css`.
- **Tokenize/Analyze/Run fails:** Open your deployment's **Functions** logs and test `/api/analyze` by using the actual UI; errors may come from the Python function, not the JavaScript frontend.
- **Old interface remains:** Confirm the desired Git branch and latest commit are the ones being deployed; then hard-refresh. Don't delete and recreate the project just to clear an old browser cache.
- **Python install error:** Confirm `requirements.txt` is in the root directory and includes Flask.
- **Preview needs authentication:** Deployment Protection can restrict the preview to authorized users; share access appropriately for the presentation.

## Public deployment caution

The local runner has a five-second child-process timeout. The Vercel in-process runner does **not** provide that same isolation or deadline. The interpreter has its own loop limit, but it is not a hardened sandbox for arbitrary untrusted programs. For a class demonstration, prefer limited access or a protected preview until you have evaluated rate limiting, resource budgets, and operational costs. Do not claim the serverless runtime has the same isolation guarantees as the local runner.

Vercel official documentation: [Flask](https://vercel.com/docs/frameworks/backend/flask), [Python runtime](https://vercel.com/docs/functions/runtimes/python), [Git deployments](https://vercel.com/docs/git).
