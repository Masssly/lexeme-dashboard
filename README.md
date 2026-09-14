# Wikidata Lexeme Edit Dashboard

Tracks the KR: *"The average number of monthly edits on Lexemes reaches
80,000 across Q3 and Q4 (Baseline January–March 2026: 66,670). As priority
languages for Abstract Wikipedia are identified, efforts are progressively
focused on these languages."*

Tracks overall Wikidata Lexeme-namespace edits per month, plus a
per-language breakdown for the four priority languages: **Dagbanli,
Malayalam, Igbo, Central Bikol**.

## Why this isn't a single GitHub Action

Lexeme edit history lives in Wikidata's MediaWiki replica database
(`revision`/`page` tables), which is only reachable from **Wikimedia Cloud
VPS / Toolforge** — not from GitHub Actions runners, which only have
regular internet access. Language assignment (which lexeme belongs to
Dagbanli vs. Malayalam etc.) is separately available via the public
**Wikidata Query Service** (SPARQL), which *is* reachable from anywhere.

So the pipeline is split:

| Step | Where it can run | Script |
|---|---|---|
| Get L-id list per language | anywhere (public SPARQL) | `scripts/get_lexeme_ids.py` |
| Count monthly edits (overall + per-language) | **Toolforge only** (replica DB) | `scripts/toolforge_update_stats.py` |
| Render dashboard | anywhere (static site) | `site/index.html` |

## Two ways to keep the data fresh

### Option A — Quick / manual (works today, no new accounts)
1. Run `queries/overall_lexeme_edits.sql` in [Quarry](https://quarry.wmcloud.org)
   against the `wikidatawiki` database.
2. Run `python3 scripts/get_lexeme_ids.py` locally (just needs Python + internet)
   to generate `queries/generated/*.sql` for each language.
3. Run each generated file in Quarry too (there may be more than one "chunk"
   file per language for large ones like Malayalam — sum same-month totals
   across chunks).
4. Paste the results into `data/lexeme_edits.json` (see
   `data/lexeme_edits.example.json` for the exact shape — **that example
   file has made-up placeholder numbers, just to show the format**).
5. Commit. The GitHub Actions workflow deploys `site/` to GitHub Pages
   automatically whenever `data/lexeme_edits.json` changes.

### Option B — Automated (requires a one-time Toolforge account)
1. Get a Toolforge account: <https://toolsadmin.wikimedia.org/>
2. `become <your-tool>`, clone this repo there, `pip install --user pymysql`.
3. Set a GitHub Personal Access Token (repo scope) as `GITHUB_TOKEN` in the
   job's environment (Toolforge Jobs Framework supports env vars/secrets).
4. Schedule the job monthly:
   ```
   toolforge jobs run update-lexeme-stats \
     --command "python3 scripts/toolforge_update_stats.py" \
     --image python3.11 \
     --schedule "0 3 1 * *"
   ```
   This does the full pipeline (SPARQL + replica DB query + writes
   `data/lexeme_edits.json` + git push) with no manual steps after setup.

Once `data/lexeme_edits.json` lands on `main`, the GitHub Actions workflow
(`.github/workflows/refresh-and-deploy.yml`) redeploys the site automatically.

## Viewing the dashboard

Enable GitHub Pages (Settings → Pages → source: GitHub Actions) on your
repo, then visit `https://<you>.github.io/<repo>/site/`. Locally, just open
`site/index.html` in a browser — it'll fall back to the example data if
`data/lexeme_edits.json` doesn't exist yet.

## Files

```
queries/overall_lexeme_edits.sql       Quarry SQL, overall edits
queries/per_language_lexeme_edits.README.md   explains the two-step approach
queries/generated/                     auto-generated per-language SQL (gitignored until run)
scripts/get_lexeme_ids.py              SPARQL fetch, public, runs anywhere
scripts/toolforge_update_stats.py      full pipeline, Toolforge only
data/lexeme_edits.example.json         schema reference (fake numbers)
data/lexeme_edits.json                 real data (you generate this)
site/index.html                        the dashboard itself (Chart.js)
.github/workflows/refresh-and-deploy.yml
```

## Language QIDs

| Language | QID |
|---|---|
| Dagbanli | Q32238 |
| Malayalam | Q36236 |
| Igbo | Q33578 |
| Central Bikol | Q33284 |
