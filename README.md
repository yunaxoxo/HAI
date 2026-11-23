# GitHub Repository, Branching & PR Workflow Guide (Issues #9–#23)

## 1. Shared Test Suite & Reference Branch Setup (For Demo Cases & Docs)
To share HAI `testcases` and updated docs with teammates without pushing directly to `main`:
1. **Create a dedicated reference/docs branch from `main`:**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b docs/demo-cases-and-workflow
   ```
2. **Stage and commit the demo cases and documentation:**
   ```bash
   git add testcases README.md
   git commit -m "docs(tests): add testcases suite and workflow guide"
   git push -u origin docs/demo-cases-and-workflow
   ```
3. **Open a Pull Request into `main`** (or keep the branch open as a shared reference until teammates pull the `.lol` test files into their local environments).

---

## 2. Standard Issue Resolution Workflow (Step-by-Step for Every Teammate)

### Step 1: Sync local `main` and branch off
Never commit directly to `main`. Always branch from an up-to-date `main`:
```bash
git checkout main
git pull origin main
git checkout -b <type>/issue-<number>-<short-slug>
```
*Branch prefixes:* `fix/` (bugs), `feat/` (enhancements & extra-credit), `test/` (unit tests), `docs/` (documentation & packaging).

### Step 2: Implement & Run Local Verification
1. **Run the Python unit test suite:**
   ```bash
   python3 -B -m unittest discover -v
   ```
2. **If you edited `frontend/*`, verify JavaScript syntax:**
   ```bash
   node --check frontend/app.js
   ```
3. **Run targeted `.lol` cases** from `testcases` plus the official professor suite (`official_suite/01_variables.lol` through `10_functions.lol`) to confirm zero regressions.

### Step 3: Commit with Conventional Commits & Push
```bash
git status
git add <modified-files>
git commit -m "<type>(<scope>): <concise description> (#<number>)"
git push -u origin <type>/issue-<number>-<short-slug>
```

### Step 4: Open a Pull Request (PR) on GitHub
- **Base:** `main` ← **Compare:** `<type>/issue-<number>-<short-slug>`
- **PR Title:** `[#<number>] <Issue Title>`
- **PR Description Template:**
   ```markdown
   ## Summary
   - Root cause / change implemented:

   ## Verification
   - [ ] `python3 -B -m unittest discover -v` passes
   - [ ] Tested target `.lol` cases: `<list cases>`
   - [ ] Official suite (`01_variables.lol`–`10_functions.lol`) checked for regressions

   Closes #<number>
   ```
- **Review & Merge:** Request review from at least **1 teammate**, resolve all review comments, and click **Squash and merge**.

---

## 3. Issue-by-Issue Branch, Owner & Verification Matrix (Issues #9–#23)

| Issue | Area / Owner | Branch Name | Commit Prefix | Required Verification | PR Keyword |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **#9** | Interpreter (@Jericko) | `fix/issue-9-function-gtfo-fallthrough-noob` | `fix(interpreter):` | `core_01`, `core_03`, `10_functions.lol` | `Closes #9` |
| **#10** | Interpreter (@Jericko) | `fix/issue-10-quoshunt-int-division` | `fix(interpreter):` | `core_02`, `01_variables.lol`, `03_arith.lol` | `Closes #10` |
| **#11** | Interpreter (@Jericko) | `fix/issue-11-function-scope-isolation` | `fix(interpreter):` | `core_04`, `10_functions.lol` | `Closes #11` |
| **#12** | Interpreter (@Jericko) | `fix/issue-12-noob-gimmeh-strict-eq-numbar` | `fix(interpreter):` | `core_05`, `core_06`, `core_08`, `core_09`, `core_13` | `Closes #12` |
| **#13** | Parser (@Desmond) | `fix/issue-13-wazzup-only-declarations` | `fix(parser):` | `core_10`, `01_variables.lol` | `Closes #13` |
| **#14** | Parser (@Desmond) | `fix/issue-14-visible-plus-separator` | `fix(parser):` | `core_11`, `bonus_06`, `02_gimmeh.lol` | `Closes #14` |
| **#15** | Parser (@Desmond) | `fix/issue-15-infinite-bool-mkay` | `fix(parser):` | `core_07`, `core_12`, `05_bool.lol`, `10_functions.lol` | `Closes #15` |
| **#16** | UI / Lexer (@Gab & 1) | `feat/issue-16-friendly-token-labels` | `feat(ui):` | `ui_01`, `node --check frontend/app.js` | `Closes #16` |
| **#17** | UI (@Gab) | `feat/issue-17-ast-json-highlight-gimmeh-echo` | `feat(ui):` | `ui_02`, `02_gimmeh.lol`, `node --check frontend/app.js` | `Closes #17` |
| **#18** | UI (@Gab) | `feat/issue-18-multi-tab-editor` | `feat(ui):` | `ui_01` + `ui_06`, `node --check frontend/app.js` | `Closes #18` |
| **#19** | UI (@Gab) | `fix/issue-19-mobile-responsive-touch-targets` | `fix(ui):` | `ui_03`–`ui_06`, `MOBILE_QA_CHECKLIST.md` | `Closes #19` |
| **#20** | Lexer / Interp (Member 1 & 3) | `feat/issue-20-yarn-escape-sequences` | `feat(lexer):` | `bonus_08`, `test_lexer.py`, `test_interpreter.py` | `Closes #20` |
| **#21** | Lexer / Parser (Member 1 & 2) | `feat/issue-21-line-continuation` | `feat(lexer):` | `bonus_09`, `test_lexer.py`, `test_parser.py` | `Closes #21` |
| **#22** | Testing (@Desmond & 3) | `test/issue-22-expand-regression-suite` | `test(suite):` | `python3 -B -m unittest discover -v` | `Closes #22` |
| **#23** | Docs / Release (All; Zo lead) | `docs/issue-23-docs-audit-submission-zip` | `docs(release):` | Clean extract & offline Windows run of `<GroupName>_<section>.zip` | `Closes #23` |

---

## 4. Merge Order, Rebase & Conflict Prevention Rules
1. **Strict 1-Issue = 1-Branch = 1-PR Rule:** Keep each issue isolated so individual changes can be reviewed, tested, or reverted cleanly without blocking teammates.
2. **Core Fixes Before Regression Suite (`#9`–`#15` → `#22`):** Merge Parser (`#13`–`#15`) and Interpreter (`#9`–`#12`) fixes into `main` *before* merging Issue `#22` (`test_parser.py` & `test_interpreter.py`) so CI/local `unittest` stays green on `main`.
3. **Sync Frontend Branches (`#16`–`#19`):** Because UI issues share `frontend/app.js` and `frontend/style.css`, run `git fetch origin && git rebase origin/main` before opening each subsequent UI PR.
4. **Never Force-Push `main`:** Only use `--force-with-lease` on your own unmerged feature branch after rebasing.

