# NemoClaw — GitHub Automation Process

> **This file is your instruction set for the current session.**
> Read this file and README_TEMPLATE.md at the start of every session before doing anything else.
> All git work happens on /workspaces/ds-projects-source unless stated otherwise.

---

## What You Are Doing

You process raw data science project folders from a private GitHub repo
(`ds-projects-source`) and push each one as a clean, professional public
GitHub repository. One folder = one public repo.

You communicate with the user entirely through Discord:
- Send notifications via `discord_alerts` webhook functions
- Wait for user replies via `discord_alerts` bot wait functions
- Never proceed to the next step without the user's Discord confirmation

---

## Folder Prefix Convention

Every folder name starts with a prefix that tells you what's inside and how to push it.
Strip the prefix when creating the kebab-case repo name.

| Prefix | Contents | Push method |
|--------|----------|-------------|
| `()` | Files for an existing GitHub repo | `git remote add origin [url]` → `git push --force` |
| `.` | `project_report.pdf` + `.ipynb`/`.py` + dataset(s) | `gh repo create` (new public repo) |
| `;` | `.ipynb` with printed outputs + `DISCARD_instructions_*.pdf` + dataset(s) | `gh repo create` (new public repo) |
| `` ` `` | `DISCARD_instructions_*.pdf` + `project_report.pdf` + `.ipynb`/`.py`/`.R` + dataset(s) | `gh repo create` (new public repo) |

**DISCARD_ files:** Never read them. Never push them. They are excluded by `.gitignore`.

### Known `()` folder URLs

| Folder | Existing repo URL |
|--------|-----------------|
| `()Assignment 2 - Building a Financial Portfolio` | https://github.com/Adarsh1313/financial-portfolio-builder-lp |
| `()SCMA Midterm` | https://github.com/Adarsh1313/queensland-tourism-regression |

For `()` folders: do NOT rename the GitHub repo. Update files + README inside only.

---

## Session Flow

### On session start — always do this first

```
1. Read this file fully
2. Read README_TEMPLATE.md fully
3. Read /workspaces/ds-projects-source/project_list.md
4. Build the list of folders with status [ ] (not started)
5. Call discord_alerts.send_session_status(remaining_folders)
6. Call discord_alerts.wait_for_folder_selection()
7. Process only the folders the user selected
```

---

## Per-Folder Processing — Follow These Steps Exactly

### STEP 1 — Scan

Read every file in the folder except DISCARD_ files.
Understand: what problem it solves, what data was used, what technique,
what results were produced.

**Metric extraction priority:**
1. Notebook output cells (printed metrics, classification reports, scores)
2. `project_report.pdf` (result tables, figures)
3. If nothing found → placeholder: `"See project_report.pdf for full results"`
   **Never invent or estimate numbers.**

**For `;` prefix (no report PDF):**
- Try notebook outputs first
- If at least one numeric metric is printed → populate Results table, note source
- If outputs are sparse → replace table with: `"See notebook for full outputs"`

### STEP 2 — Rename files

- Strip the prefix from the folder name before deriving anything
- Rename all non-DISCARD files to professional snake_case
- `project_report.pdf` stays as-is
- Notebook: `[technique]_[task].ipynb`
- Script: descriptive name matching what it does
- Dataset: descriptive name matching data content
- R files: `[technique]_[task].R`

### STEP 3 — Build flat structure

All files at root level. Create these new files:
- `README.md` — follow README_TEMPLATE.md exactly
- `requirements.txt` — extracted from all imports in `.py` and `.ipynb` files
- `.gitignore` — standard Python/R gitignore, plus: `DISCARD_*` and `.env`

### STEP 4 — Generate README.md

Follow README_TEMPLATE.md. Every section must be filled.
No course names, assignment numbers, professor names, or university context anywhere.

### STEP 5 — Output summary + Discord notification

Collect:
- Suggested repo name (kebab-case, no prefix, no course codes)
- Every file rename: old name → new name
- Where metrics were found (notebook / PDF / not found)
- Any files you were unsure about
- Anything the user should manually review

Then call:
```python
discord_alerts.send_folder_summary(
    folder_name, repo_name, renamed_files, metrics_source, warnings
)
```

Then call `discord_alerts.wait_for_approval()` and block.
- If `"proceed"` → go to Push step
- If `"skip"` → skip this folder, update project_list.md status to `[skip]`, move to next

---

## Push to GitHub

### New repos (`.` `;` `` ` `` prefix)

```bash
cd /workspaces/ds-projects-source/[renamed-folder]
git init
git add .
git commit -m "Initial commit: [Professional Project Title]

[One sentence: technique used]
[One sentence: outcome or business value]"
gh repo create [repo-name] --public --source=. --push
```

Then call:
```python
discord_alerts.send_github_alert(repo_name, repo_url, description, prefix_type)
```

### Existing repos (`()` prefix)

```bash
cd /workspaces/ds-projects-source/[folder-name]
git init
git remote add origin [url-from-project_list.md]
git add .
git commit -m "Restructure: standardised filenames and README

README added with methodology, results, future scope.
Files renamed to snake_case. requirements.txt and .gitignore added."
git push --force origin main
```

Then call:
```python
discord_alerts.send_github_alert(repo_name, existing_url, description, "()")
```

---

## After Each Successful Push

Update `project_list.md` — change the folder's status from `[ ]` to `[x]`:

```bash
cd /workspaces/ds-projects-source
# edit project_list.md status column
git add project_list.md
git commit -m "status: mark [repo-name] as done"
git push origin main
```

Then move to the next selected folder. Repeat from STEP 1.

---

## End of Session

After all selected folders are processed, call:
```python
discord_alerts.send_session_complete(pushed, skipped, errors)
```

---

## Error Handling

If any step fails:
1. Call `discord_alerts.send_error_alert(error_msg)` immediately
2. Do not proceed to the next folder
3. Wait — the user will restart the session and tell you how to continue

---

## README Quality Rules (Apply to Every Project)

- Audience: a data scientist reading now + an engineer reading later
- Results section: always explain what the metric *means* before showing the number
- Never mention: university, course, assignment number, semester, professor
- Future Scope: engineering next steps only — not academic extensions
- Tech Stack: be specific — not "pandas" but "pandas — data cleaning and feature engineering"
- Methodology: plain English — no unexplained acronyms
