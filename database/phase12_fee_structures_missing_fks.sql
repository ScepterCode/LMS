-- Phase 12: restore the two missing foreign keys on fee_structures.
--
-- Same root cause as the earlier phase10 investigation: fee_structures.
-- class_id -> classes and fee_structures.session_id -> academic_sessions
-- were defined in the original phase3_fees_schema.sql migration but were
-- never actually applied to the live database. Without them, PostgREST
-- can't resolve embedded joins like "fee_structures?select=*,classes(name)",
-- and any endpoint using that join 500s with PGRST200
-- ("Could not find a relationship between 'fee_structures' and 'classes'").
--
-- This surfaced live as the "Add Fee Structure" / Fee Management page
-- failing to load (GET /api/v1/fees/structures returning 500). The
-- endpoint itself has already been rewritten to do manual batched lookups
-- instead of relying on the embed, so it no longer needs this constraint
-- to function - but the constraint is still worth adding for real
-- referential integrity going forward.
--
-- The two rows that were blocking this (orphaned class_id/session_id
-- values from a throwaway test org) have already been deleted, so this
-- should apply cleanly.

ALTER TABLE fee_structures ADD CONSTRAINT fee_structures_class_id_fkey
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE;

ALTER TABLE fee_structures ADD CONSTRAINT fee_structures_session_id_fkey
    FOREIGN KEY (session_id) REFERENCES academic_sessions(id) ON DELETE CASCADE;

NOTIFY pgrst, 'reload schema';
