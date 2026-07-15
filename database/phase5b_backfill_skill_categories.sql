-- Phase 5b: backfill default skill categories for organizations that
-- registered after the original phase5 migration ran.
--
-- phase5_report_card_enhancements.sql seeded the 7 default psychomotor/
-- affective traits only for organizations that existed at the time it was
-- applied. Nothing seeded them going forward for schools created afterwards
-- via /auth/register-school or the system-admin assisted onboarding
-- endpoint - every one of those schools got an empty, unconfigured skills
-- list (Report Card Skills page showed "No traits yet" in both domains,
-- and report cards had no skills section at all).
--
-- This has since been fixed at the application level: both org-creation
-- paths now call seed_default_skill_categories() (backend/app/api/v1/
-- endpoints/skills.py) at creation time. This script is the one-time
-- backfill for organizations that were created before that fix shipped -
-- safe to re-run (ON CONFLICT DO NOTHING), and safe to run on any
-- environment where this gap might exist (e.g. a staging copy of this DB).

INSERT INTO skill_categories (organization_id, name, domain, display_order)
SELECT o.id, t.name, t.domain, t.display_order
FROM organizations o
CROSS JOIN (
    VALUES
        ('Sports & Games', 'psychomotor', 1),
        ('Handling of Tools/Equipment', 'psychomotor', 2),
        ('Handwriting', 'psychomotor', 3),
        ('Musical Skills', 'psychomotor', 4),
        ('Punctuality', 'affective', 1),
        ('Neatness', 'affective', 2),
        ('Honesty', 'affective', 3)
) AS t(name, domain, display_order)
ON CONFLICT (organization_id, name) DO NOTHING;
