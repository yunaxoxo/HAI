# Deployment

HAI runs locally using only Python's standard library. Hosted deployments use Flask via Vercel, with a **different execution-isolation model** (see [Security](#security-and-runtime-limits)).

## Local development

```bash
python3 -B -m unittest discover -q
python3 -B app.py
```

Visit `http://127.0.0.1:8000`. A Node.js build step is not required. You can optionally validate the frontend with `node --check frontend/app.js`.

## Vercel (GitHub integration)

1. Connect your repository to an existing Vercel project, or import it at [vercel.com/new](https://vercel.com/new).
2. Set the **Root Directory** to the repository root. Keep the included `vercel.json`, `api/index.py`, and `requirements.txt` together.
3. Configure the intended Production branch (normally `main`). Feature branches receive Previews; merges to the Production branch create Production deployments when Git integration is active.
4. Open the **Preview** for your feature branch and test it before merging.

From a linked local folder, `vercel deploy` creates a Preview; `vercel deploy --prod` explicitly targets Production. Do not deploy manually to Production merely to test a branch.

## Validate the deployed build

In the browser's Developer Tools → Network panel, confirm these paths return **200**, correct response bodies, and correct MIME types:

| URL | Expected Content-Type |
| --- | --- |
| `/favicon.ico?v=4` | `image/vnd.microsoft.icon` |
| `/favicon.svg?v=4` | `image/svg+xml` |
| `/favicon-32x32.png?v=4` | `image/png` |
| `/apple-touch-icon.png?v=4` | `image/png` |
| `/vendor/codemirror.js` | JavaScript |
| `/vendor/codemirror.css` | CSS |
| `/app.js` and `/style.css` | JavaScript and CSS |

Verify **Run**, **Tokenize**, **Analyze**, AST source navigation, **Launch editor**, keyboard help (`?`), and `GIMMEH`. On mobile check Code, Explore, and Output. A hard refresh or private window may be necessary because browsers aggressively cache favicons.

If favicon requests return HTML or 404, the deployed branch may lack the new assets, or the Flask adapter/static routing may be out of date. Inspect the deployed Git commit and the Vercel Functions logs before changing configuration.

## Security and runtime limits

The local runner enforces a **five-second child-process timeout**. On Vercel, source code executes **in-process**, without an equivalent hard per-program deadline or isolation. Interpreter loop limits are not a substitute for sandboxing. For public use, evaluate resource and input limits, abuse protections, and deployment access restrictions. Keep early previews appropriately access-controlled.

## Troubleshooting

- **Preview differs from Production:** compare the Git commit hash, branch, and build source in Vercel Deployments. CLI deployments can include uncommitted local files.
- **Blank page or missing files:** check Vercel build logs and root directory. With the included custom `builds` configuration, confirm static assets are included in the deployed Python function.
- **404 icons:** verify the `frontend/` icon files are tracked (`git ls-files frontend`) and that the Flask routes serve image content rather than a page fallback.
- **API failures:** check Function logs and the `/api/*` network responses.

Reference: [Vercel Flask deployment documentation](https://vercel.com/docs/frameworks/backend/flask).
