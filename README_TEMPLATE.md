# NemoClaw — README Template for Data Science Projects

> **How to use this file:**
> This is the master template NemoClaw uses when generating `README.md` for every project.
> It lives in the root of `ds-projects-source` as a reference.
> When adding a new project folder manually, the prefix you give the folder controls
> which variant NemoClaw uses (see Prefix Rules below).

---

## Prefix Rules (Folder Naming Convention)

| Prefix | Meaning | What's inside |
|--------|---------|---------------|
| `()` | Existing GitHub repo — force push | Existing remote URL, standardize files + README only |
| `.` | Report + code + data | `project_report.pdf`, `.ipynb` or `.py`, dataset(s) |
| `;` | Code with printed outputs, no report | `.ipynb` with outputs in cells, `DISCARD_instructions_*.pdf`, dataset(s) |
| `` ` `` | Two PDFs + code + data | `DISCARD_instructions_*.pdf`, `project_report.pdf`, `.ipynb` or `.py` or `.R`, dataset(s) |

**Naming format:** `[PREFIX][Original folder name]`
**Examples:** `.BDA Exam1`, `;Text Analytics HW2`, `` `Assignment 3.1 - Organic Food Supply Chain ``

NemoClaw strips the prefix entirely when creating the kebab-case repo name.
The prefix is stored only in `project_list.md` as metadata.

---

## README.md Template

> NemoClaw pastes the section below verbatim and fills in every `[placeholder]`.
> Rules for each section follow in the Generation Notes.

---

```markdown
# [Professional Project Title]

> [One sentence: what problem + what data + what technique. No course names, no assignment numbers.]

---

## Problem Statement

[2–3 sentences. Write for a business stakeholder, not a professor.
What real-world decision does this model enable?
What goes wrong without it?]

---

## Dataset

| Property | Detail |
|----------|--------|
| Source | [where data came from — if academic/synthetic, say "Simulated dataset for supply chain scenario"] |
| Size | [rows × columns if visible in code or notebook] |
| Key Features | [2–4 most important input variables] |
| Target Variable | [what we're predicting, optimising, or measuring] |

---

## Methodology

[What technique was used and WHY it fits this problem.
Write in plain English. No unexplained acronyms.
Good pattern: "[Technique] works by [mechanism], which fits here because [reason specific to this data/problem]."]

---

## Results

[ALWAYS lead with what the numbers mean before showing them.
Pattern: "The model [did X] [metric value]% of the time — meaning [plain English consequence]."]

| Metric | Score | What It Means |
|--------|-------|---------------|
| [metric] | [value] | [one plain English sentence] |
| [metric] | [value] | [one plain English sentence] |

<!-- PREFIX-SPECIFIC RULES (NemoClaw handles automatically):

  '.' prefix  — metrics from project_report.pdf or notebook outputs.
                Note source: "Metrics from project_report.pdf" or "Metrics from notebook outputs".

  ';' prefix  — no report PDF. Read printed outputs in notebook cells.
                If outputs are rich enough: populate table normally, note "Metrics from notebook cell outputs".
                If outputs are sparse (no numeric results): replace table with:
                "See notebook for full outputs — results are embedded in cell outputs below each code block."

  '`' prefix  — two PDFs present. project_report.pdf is the source of truth.
                DISCARD_ file must be ignored entirely.

  '()' prefix — existing repo being updated. Preserve any existing results if already documented.
                Only overwrite if you found more accurate/complete metrics in the files.
-->

---

## Key Findings

- [Most important insight — the single thing a stakeholder should remember]
- [Something surprising or non-obvious from the results]
- [Business implication — what action should someone take based on this?]

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.x | Core language |
| [library] | [specific thing it was used for in this project] |
| [library] | [specific thing it was used for in this project] |

<!-- If R was used (common in '`' prefix folders): replace Python with R and list R packages -->

---

## How to Run

```bash
git clone https://github.com/[username]/[repo-name]
cd [repo-name]
pip install -r requirements.txt
jupyter notebook [notebook-name].ipynb
```

<!-- If R: replace pip line with  Rscript -e "install.packages(c(...))"  and final line with  Rscript [script-name].R -->

---

## Future Scope

- [Data improvement that would directly increase model performance or coverage]
- [Engineering step that would make this production-ready or deployable]
- [Next business question this analysis could naturally extend to answer]
```

---

## Generation Notes for NemoClaw

### On titles
- Must be a professional project title — no course codes, no assignment numbers, no professor names.
- Good: `Supply Chain Optimization with Linear Programming`
- Bad: `Assignment 3.1 - SCMA 632 Optimization HW`

### On the Results section — metric extraction priority
1. Check notebook output cells first (printed metrics, sklearn reports, etc.)
2. If not in outputs, read `project_report.pdf` for result tables or figures
3. Note which source metrics came from in an HTML comment above the table
4. If nothing found anywhere: `"See project_report.pdf for full results."` — never invent numbers

### On the `;` prefix Results fallback
- "Sparse" means: no numeric metrics visible, only print statements of intermediate steps
- "Rich enough" means: at least one numeric accuracy/score/metric is printed
- When falling back: replace the entire table with the one-line placeholder, do not leave an empty table

### On the `()` prefix
- Do NOT rename the GitHub repo — only update files and README inside
- The remote URL is embedded in the folder name convention and in `project_list.md`
- Use: `git remote add origin [url]` then `git push --force origin main`

### On R projects
- R files appear mainly in `` ` `` prefix folders (two PDFs)
- Replace Python-specific README sections with R equivalents
- `requirements.txt` becomes `packages.R` with `install.packages(c(...))`
- Add both to `.gitignore` boilerplate appropriately

### On the DISCARD_ files
- Files prefixed `DISCARD_` are homework instruction sheets — skip entirely
- Never read them for content, never reference them in README
- They are excluded by `.gitignore` and deleted from the repo after your confirmation on Discord

### Consistency rules across all READMEs
- Audience: data scientists reading now, engineers reading later
- Never mention: university, course name, assignment number, semester, professor
- Future Scope: engineering next steps only — not "collect more data for the class project"
- Tech Stack: be specific — not just "pandas" but "pandas — data cleaning and feature engineering"
