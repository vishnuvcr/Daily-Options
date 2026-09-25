from __future__ import annotations

import csv
import json
from pathlib import Path

summary = json.loads(Path("reports/phase29_2_summary.json").read_text(encoding="utf-8"))
rows = list(csv.DictReader(Path("reports/phase29_2_contract_coverage_matrix.csv").open(encoding="utf-8", newline="")))

checks = {
    "candidate_rows": summary.get("candidate_rows") == 71,
    "matrix_rows": len(rows) == 71 and summary.get("matrix_row_count") == 71,
    "backtest_allowed": summary.get("backtest_allowed") == 0,
    "archive_discovered_videos": summary.get("archive_discovered_videos") == 169,
    "archive_transcripts_status_archived": summary.get("archive_transcripts_status_archived") == 169,
    "candidate_archive_provenance": summary.get("candidate_archive_provenance") == 71,
    "all_rows_backtest_no": summary.get("all_rows_backtest_no") is True and all(r.get("backtest_allowed") == "NO" for r in rows),
}

print(json.dumps({"checks": checks, "summary": summary}, indent=2))
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("Phase 29.2 hard gate failed: " + ", ".join(failed))
print("Phase 29.2 hard gate: PASS")
