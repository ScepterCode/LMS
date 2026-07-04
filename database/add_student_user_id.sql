-- ============================================
-- MIGRATION: Add user_id column to students table
-- ============================================
-- This allows students to have login accounts

-- Step 1: Add the user_id column (nullable initially)
ALTER TABLE students 
ADD COLUMN user_id UUID UNIQUE REFERENCES users(id) ON DELETE SET NULL;

-- Step 2: Create index for faster lookups
CREATE INDEX idx_students_user_id ON students(user_id);

-- Step 3: Add comment for documentation
COMMENT ON COLUMN students.user_id IS 'Optional reference to users table - allows student to login if set';

-- ============================================
-- VERIFICATION
-- ============================================

-- Check the column was added
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'students' AND column_name = 'user_id';

-- Check the foreign key constraint exists
SELECT
    tc.constraint_name, 
    tc.table_name, 
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.table_name = 'students' 
    AND tc.constraint_type = 'FOREIGN KEY'
    AND kcu.column_name = 'user_id';

-- Check the index was created
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'students' AND indexname = 'idx_students_user_id';

-- Sample query to show students with and without user accounts
SELECT 
    s.id,
    s.admission_number,
    s.first_name,
    s.last_name,
    s.user_id,
    CASE 
        WHEN s.user_id IS NOT NULL THEN 'Has Login'
        ELSE 'No Login'
    END as login_status,
    u.email as user_email
FROM students s
LEFT JOIN users u ON s.user_id = u.id
LIMIT 10;

-- ============================================
-- ROLLBACK (if needed)
-- ============================================
-- Uncomment the following lines to rollback this migration:

-- DROP INDEX IF EXISTS idx_students_user_id;
-- ALTER TABLE students DROP COLUMN IF EXISTS user_id;
