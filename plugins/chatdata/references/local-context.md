# Local context for one project

ChatData can create a visible `chatdata-context/` folder inside a project you choose. It helps a future session find the metric definitions, local evidence, and checks that you decided were safe to reuse. It never scans your whole computer or client chat history.

Setup looks only at file metadata from the chosen directory and its ordinary subdirectories. It includes supported files modified in the last 30 days by default. “Modified” means the filesystem modification time; it does not prove that you opened, ran, or relied on a file. Setup does not read source contents, move originals, change originals, upload anything, or make a network request. Relative filenames intentionally appear in the private local inventory. Sensitive-looking files, hidden directories, dependency folders, symlinks, and unsupported files are skipped. Read `inventory.json` coverage before concluding that an absent file does not exist.

## Create the folder

Resolve `scripts/local_context.py` from the installed ChatData plugin, then run:

```sh
python3 "<resolved plugin root>/scripts/local_context.py" init --root "<project directory>" --days 30
```

The project directory is required. Do not substitute a home directory, filesystem root, `~/.claude`, or `~/.codex`. ChatData refuses those locations and refuses a symlink root. It also refuses to overwrite an existing `chatdata-context/` folder.

Setup creates:

- `inventory.json`: bounded metadata for recently modified analysis files, including coverage gaps and skipped-file counts.
- `semantic-model.json`: a draft semantic model, initially empty.
- `trust.json`: metric-specific definitions and local proof, initially empty.
- `README.md`: the review steps for this project.
- `index.html`: a local, readable inventory view.
- `.gitignore`: keeps the entire folder private by default.

These files organize context; they are not evidence by themselves. Do not commit or upload the folder unless the user separately decides to share it.

To refresh the 30-day inventory later without replacing reviewed context, run:

```sh
python3 "<resolved plugin root>/scripts/local_context.py" refresh --root "<project directory>" --days 30
```

Refresh atomically replaces only `inventory.json` and `index.html`. It first checks the local context files for unsafe paths, preserves `semantic-model.json`, `trust.json`, and `README.md`, and excludes `chatdata-context/` from its own inventory. Review any new coverage gap and rerun the metric check afterward.

## Apache Ossie profile

`semantic-model.json` follows the bundled snapshot of the Apache Ossie Open Semantic Interchange core JSON Schema, version `0.2.0.dev0`. ChatData pins that draft so local checks do not change underneath an analysis. The bundled validator implements only the JSON Schema features used by that pinned file and fails closed if the schema begins using something it does not understand. Passing it means the JSON has the expected structure. It is not the official full Apache Ossie validator, proof of compatibility with every Ossie consumer, or approval of any metric.

A small model can look like this:

```json
{
  "version": "0.2.0.dev0",
  "semantic_model": [
    {
      "name": "product_analytics",
      "datasets": [
        {
          "name": "accounts",
          "source": "analytics.accounts"
        }
      ],
      "metrics": [
        {
          "name": "weekly_active_accounts",
          "description": "Accounts with at least one qualifying activity during the reporting week.",
          "datatype": "Integer",
          "expression": {
            "dialects": [
              {
                "dialect": "ANSI_SQL",
                "expression": "COUNT(DISTINCT CASE WHEN is_qualifying_activity THEN account_id END)"
              }
            ]
          }
        }
      ]
    }
  ]
}
```

Treat names and expressions as drafts until the user reviews the business meaning and source mapping.

## Add proof without inventing approval

For every metric that should support a canonical answer, add an exact-name entry to `trust.json`. Fingerprint each chosen source and check artifact separately:

```sh
python3 "<resolved plugin root>/scripts/local_context.py" fingerprint --root "<project directory>" --path "sql/weekly-active-accounts.sql"
python3 "<resolved plugin root>/scripts/local_context.py" fingerprint --root "<project directory>" --path "analysis/weekly-active-accounts/checks.json"
```

Paths must be relative to the selected project. The helper refuses remote paths, symlinks, files outside the project, non-regular files, and files larger than its verification limit. A fingerprint says only that the local bytes match later; it does not make the source correct.

After editing `semantic-model.json`, calculate its canonical hash with the dedicated command:

```sh
python3 "<resolved plugin root>/scripts/local_context.py" semantic-hash --root "<project directory>"
```

Use the returned `semantic_sha256` in the trust record. Do not substitute the ordinary file fingerprint; that includes formatting whitespace and is intentionally different.

The trust record has this shape. The values are illustrative and will not pass for a real project until the names, hashes, dates, definition, and evidence match local files. Set `reviewed_by_user` to `true` and record `reviewed_at` only after the user actually reviews the entry. Never infer approval from an old analysis, a filename, or structural validation.

```json
{
  "schema_version": 1,
  "metrics": {
    "weekly_active_accounts": {
      "definition": "Distinct eligible accounts with at least one qualifying human activity in the reporting week.",
      "unit": "account",
      "population": "non-test accounts active before the end of the reporting week",
      "timezone": "America/Los_Angeles",
      "window": "Monday 00:00 through the following Monday 00:00, event time",
      "exclusions": "test accounts, employees, bots, deleted events",
      "null_policy": "exclude activity with a null account_id; report its count as a data-quality check",
      "grain": "one row per account per reporting week",
      "reviewed_by_user": true,
      "reviewed_at": "2026-09-07T17:00:00-07:00",
      "semantic_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "sources": [
        {
          "dataset": "accounts",
          "path": "sql/weekly-active-accounts.sql",
          "sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "checked_at": "2026-09-07T16:45:00-07:00",
          "valid_until": "2026-10-07T16:45:00-07:00"
        }
      ],
      "checks": [
        {
          "name": "weekly result reconciles to the approved dashboard",
          "status": "passed",
          "evidence_path": "analysis/weekly-active-accounts/checks.json",
          "evidence_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
        }
      ],
      "unresolved_conflicts": [],
      "caveats": [
        "Late events can revise the latest week until the source closes."
      ]
    }
  }
}
```

Each source's `dataset` must exactly match a dataset in the same Ossie semantic model as the metric. The semantic hash is the SHA-256 of canonical JSON: UTF-8, object keys sorted, no extra spaces, and non-ASCII characters preserved.

## Check before a canonical metric answer

Run the exact metric name:

```sh
python3 "<resolved plugin root>/scripts/local_context.py" check --root "<project directory>" --metric "weekly_active_accounts"
```

`ready_for_analysis` means the metric exists exactly once in the pinned semantic model; the local trust entry is complete and actually marked reviewed; source and evidence files still match their recorded hashes; checks are marked passed; review and freshness dates are valid; and no conflict remains unresolved. It does not prove the definition, method, or future answer is true.

If the result is `blocked`, stop before giving a canonical metric answer. Show every returned gap in plain language and the next local action: locate the missing definition or source, resolve a conflicting definition, rerun a failed check, refresh stale evidence, update a changed fingerprint, or ask the user to review the drafted entry. Run the same check again after the gaps are fixed. Do not fill missing values from guesswork, mark a check passed without evidence, or fabricate user review.

Blocking applies to a requested canonical metric answer. The user can still ask for exploratory work, inspect an unfamiliar file, or run the bundled synthetic example. Label that work exploratory or synthetic and do not present it as the approved business metric.
