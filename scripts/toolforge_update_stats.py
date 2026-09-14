#!/usr/bin/env python3
"""
Run this on Toolforge (NOT on GitHub Actions — GitHub's runners cannot reach
the Wikimedia Cloud-VPS-internal replica database; only Toolforge/Cloud VPS
can). It does the full pipeline in one go:

  1. Pulls current L-id lists per target language from WDQS (SPARQL).
  2. Queries the wikidatawiki replica DB directly for monthly Lexeme-namespace
     edit counts, both overall and restricted to each language's ID list.
  3. Writes data/lexeme_edits.json.
  4. Commits and pushes that file to your GitHub repo.

One-time setup on Toolforge:
  - Create a tool account: https://toolsadmin.wikimedia.org/
  - `become <your-tool-name>`
  - `git clone <your GitHub repo URL> repo && cd repo`
  - `toolforge webservice ... ` not needed here — this is a batch job, not a webservice.
  - `pip install --user pymysql` (or use a venv / Toolforge's Python image)
  - Set a GitHub Personal Access Token (repo scope) as an env var, e.g. by
    adding it to a `.env` file this script loads, or exporting it in the
    job's environment. NEVER commit the token itself.
  - Schedule it (monthly, 1st of month at 03:00 UTC):
      toolforge jobs run update-lexeme-stats \\
        --command "python3 scripts/toolforge_update_stats.py" \\
        --image python3.11 \\
        --schedule "0 3 1 * *"

Replica DB credentials are auto-provided at ~/replica.my.cnf on Toolforge —
no password handling needed in this script.
"""
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict

import pymysql

LANGUAGES = {
    "Dagbanli": "Q32238",
    "Malayalam": "Q36236",
    "Igbo": "Q33578",
    "Central Bikol": "Q33284",
}

TARGET_MONTHLY_EDITS = 80000
BASELINE = {"start": "2026-01", "end": "2026-03", "average": 66670}
START_TIMESTAMP = "20260101000000"

REPLICA_HOST = "wikidatawiki.analytics.db.svc.wikimedia.cloud"
REPLICA_DB = "wikidatawiki_p"
REPLICA_CNF = os.path.expanduser("~/replica.my.cnf")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT, "data", "lexeme_edits.json")

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")  # set this in the job's env
GIT_USER_NAME = os.environ.get("GIT_USER_NAME", "lexeme-stats-bot")
GIT_USER_EMAIL = os.environ.get("GIT_USER_EMAIL", "lexeme-stats-bot@example.invalid")


def fetch_lexeme_ids(qid: str) -> list[str]:
    query = f"SELECT ?lexeme WHERE {{ ?lexeme dct:language wd:{qid} . }}"
    url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode(
        {"query": query, "format": "json"}
    )
    req = urllib.request.Request(url, headers={
        "User-Agent": "dagbanli-lexeme-dashboard/1.0 (toolforge cron)",
        "Accept": "application/sparql-results+json",
    })
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.load(resp)
    return [row["lexeme"]["value"].rsplit("/", 1)[-1] for row in data["results"]["bindings"]]


def monthly_counts(cursor, page_titles: list[str] | None) -> dict[str, int]:
    base_sql = """
        SELECT LEFT(rev_timestamp, 6) AS month, COUNT(*) AS edit_count
        FROM revision
        JOIN page ON revision.rev_page = page.page_id
        WHERE page.page_namespace = 146
          AND rev_timestamp >= %s
    """
    params = [START_TIMESTAMP]

    if page_titles is None:
        sql = base_sql + " GROUP BY month ORDER BY month"
        cursor.execute(sql, params)
    else:
        # Batch to keep individual queries reasonably sized.
        totals: dict[str, int] = defaultdict(int)
        CHUNK = 3000
        for i in range(0, len(page_titles), CHUNK):
            chunk = page_titles[i:i + CHUNK]
            placeholders = ",".join(["%s"] * len(chunk))
            sql = base_sql + f" AND page.page_title IN ({placeholders}) GROUP BY month"
            cursor.execute(sql, params + chunk)
            for month, count in cursor.fetchall():
                totals[month] += count
        return dict(sorted(totals.items()))

    return {month: count for month, count in cursor.fetchall()}


def month_fmt(yyyymm: str) -> str:
    return f"{yyyymm[:4]}-{yyyymm[4:6]}"


def main():
    conn = pymysql.connect(
        host=REPLICA_HOST,
        db=REPLICA_DB,
        read_default_file=REPLICA_CNF,
        charset="utf8mb4",
    )
    cursor = conn.cursor()

    print("Overall Lexeme edits...")
    overall_raw = monthly_counts(cursor, None)
    overall = [{"month": month_fmt(m), "edits": c} for m, c in sorted(overall_raw.items())]

    languages_out = {}
    for lang, qid in LANGUAGES.items():
        print(f"{lang} ({qid})...")
        ids = fetch_lexeme_ids(qid)
        print(f"  {len(ids)} lexemes")
        raw = monthly_counts(cursor, ids)
        languages_out[lang] = {
            "qid": qid,
            "lexeme_count": len(ids),
            "months": [{"month": month_fmt(m), "edits": c} for m, c in sorted(raw.items())],
        }
        time.sleep(1)

    cursor.close()
    conn.close()

    output = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "overall": {
            "target": TARGET_MONTHLY_EDITS,
            "baseline": BASELINE,
            "months": overall,
        },
        "languages": languages_out,
    }

    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Wrote {DATA_PATH}")

    push_to_github()


def push_to_github():
    if not GITHUB_TOKEN:
        print("GITHUB_TOKEN not set — skipping git push. Data file was still updated locally.")
        return
    run = lambda *args: subprocess.run(args, cwd=ROOT, check=True)
    try:
        run("git", "config", "user.name", GIT_USER_NAME)
        run("git", "config", "user.email", GIT_USER_EMAIL)
        run("git", "add", "data/lexeme_edits.json")
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"], cwd=ROOT
        )
        if result.returncode == 0:
            print("No changes to commit.")
            return
        run("git", "commit", "-m", "Automated monthly lexeme edit stats update")
        run("git", "push")
        print("Pushed updated stats to GitHub.")
    except subprocess.CalledProcessError as e:
        print(f"Git push failed: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
