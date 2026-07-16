"""Poor-man's backup: dumps every table to a timestamped JSON file.

The current Supabase plan has no point-in-time recovery, so this is the
only safety net until that changes. Run it periodically (manually, or
wired into a scheduled task) from the repo root:

    .venv/Scripts/python.exe database/backup_export.py

Output goes to database/backups/<UTC timestamp>/<table>.json (gitignored).
To restore a table: read the JSON and re-insert rows via the Supabase
Python client - there is no automated restore path, this is dump-only.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
from app.core.database import get_supabase

TABLES = [
    "organizations", "campuses", "users", "students", "teachers", "parents",
    "classes", "subjects", "academic_sessions", "terms", "class_subjects",
    "teacher_class_assignments", "student_guardians", "parent_student_links",
    "assessments", "grades", "subject_grades", "report_cards",
    "grade_configs", "grading_schemes", "grading_scheme_components",
    "student_remarks", "student_skill_ratings", "skill_categories",
    "attendance_records", "attendance_summaries", "leave_requests",
    "teacher_attendance", "student_fees", "fee_categories", "payments",
    "subject_assignments", "class_enrollments", "subscription_plans",
    "audit_logs", "school_reports", "school_report_recipients",
]

PAGE_SIZE = 1000


def fetch_all(sb, table: str) -> list[dict]:
    rows: list[dict] = []
    start = 0
    while True:
        res = sb.table(table).select("*").range(start, start + PAGE_SIZE - 1).execute()
        rows.extend(res.data)
        if len(res.data) < PAGE_SIZE:
            break
        start += PAGE_SIZE
    return rows


def main() -> None:
    sb = get_supabase()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(__file__).resolve().parent / "backups" / stamp
    out_dir.mkdir(parents=True, exist_ok=True)

    total_rows = 0
    for table in TABLES:
        try:
            rows = fetch_all(sb, table)
        except Exception as exc:
            print(f"  {table}: SKIPPED ({exc})")
            continue
        (out_dir / f"{table}.json").write_text(json.dumps(rows, indent=2, default=str))
        total_rows += len(rows)
        print(f"  {table}: {len(rows)} rows")

    print(f"\nBackup written to {out_dir} ({total_rows} rows total)")


if __name__ == "__main__":
    main()
