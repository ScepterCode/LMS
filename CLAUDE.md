# Working on this repo

This is a **live production system with real onboarded schools** (Supabase project, no PITR/backup on the current plan). There is no undo. Follow these rules without exception:

## Database safety

- **Never run a DELETE, TRUNCATE, DROP, or UPDATE against the live Supabase database that isn't scoped to a specific, already-known row id or a single throwaway `organization_id` you created for testing.** A filter like `.neq("id", "<sentinel-that-never-matches>")` is not a scope — it matches every row. If you can't name the exact id(s) affected before running the command, don't run it.
- **Never write or run a "reset/seed/clear test data" script against the live database.** If you need a clean slate to test something, create a new throwaway organization, test against only that org's rows, then delete only those rows by id when done.
- **Schema changes that could touch existing rows (changing a constraint, retyping a column, adding NOT NULL) must use `ALTER TABLE`, never `DROP TABLE` / recreate.** Verify the exact ALTER against a throwaway org first if there's any doubt about its effect on existing rows.
- **Ad-hoc diagnostic/fix scripts belong in the scratchpad or a reviewed `database/*.sql` migration — not as unreviewed one-off Python hitting the live DB.** Before running anything with `.delete(`, `.update(`, or raw SQL against tables that hold real school data, state in chat exactly which rows/orgs will be affected and get a yes.
- Direct psql/`DATABASE_URL` access does not work from this dev environment — all schema migrations go through the Supabase SQL Editor, run by the user. Never assume a migration applied just because you wrote the file; verify row/constraint state afterward via the Python client.
- This project's own `.delete()` calls in `backend/app/api/v1/endpoints/*.py` and `backend/tests/conftest.py` are all scoped to a single id or a single org — keep that invariant. Any new delete you add must be equally scoped.

## Concurrent sessions

Multiple Claude sessions may run against this same repo/database at once (background tasks, the user's other terminals). Assume another session could be writing to the same live database concurrently. Don't run anything destructive without confirming scope in chat first, even if it seems like "just cleanup."

## Backups

There's no managed backup on the current Supabase plan. `database/backup_export.py` dumps all tables to timestamped JSON for a manual safety net — see its header for usage. Recommend the user run it periodically (or upgrade the Supabase plan for real PITR) rather than relying on it as a substitute.
