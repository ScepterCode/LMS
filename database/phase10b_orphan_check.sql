-- Diagnostic only - run this and share the result. It counts, for every
-- FK that phase10 could not add, how many rows have a value that doesn't
-- match any row in the parent table (i.e. orphaned - almost certainly
-- leftover from throwaway test schools created/deleted during
-- development, since without the FK constraint, deleting the parent
-- never cascaded to clean these up).

SELECT 'assessments.subject_id' AS col, count(*) FROM assessments a LEFT JOIN subjects s ON s.id = a.subject_id WHERE a.subject_id IS NOT NULL AND s.id IS NULL
UNION ALL SELECT 'assessments.class_id', count(*) FROM assessments a LEFT JOIN classes c ON c.id = a.class_id WHERE a.class_id IS NOT NULL AND c.id IS NULL
UNION ALL SELECT 'assessments.session_id', count(*) FROM assessments a LEFT JOIN academic_sessions x ON x.id = a.session_id WHERE a.session_id IS NOT NULL AND x.id IS NULL
UNION ALL SELECT 'assessments.term_id', count(*) FROM assessments a LEFT JOIN terms t ON t.id = a.term_id WHERE a.term_id IS NOT NULL AND t.id IS NULL
UNION ALL SELECT 'grades.student_id', count(*) FROM grades g LEFT JOIN students s ON s.id = g.student_id WHERE g.student_id IS NOT NULL AND s.id IS NULL
UNION ALL SELECT 'subject_grades.student_id', count(*) FROM subject_grades g LEFT JOIN students s ON s.id = g.student_id WHERE g.student_id IS NOT NULL AND s.id IS NULL
UNION ALL SELECT 'subject_grades.subject_id', count(*) FROM subject_grades g LEFT JOIN subjects s ON s.id = g.subject_id WHERE g.subject_id IS NOT NULL AND s.id IS NULL
UNION ALL SELECT 'subject_grades.class_id', count(*) FROM subject_grades g LEFT JOIN classes c ON c.id = g.class_id WHERE g.class_id IS NOT NULL AND c.id IS NULL
UNION ALL SELECT 'subject_grades.session_id', count(*) FROM subject_grades g LEFT JOIN academic_sessions x ON x.id = g.session_id WHERE g.session_id IS NOT NULL AND x.id IS NULL
UNION ALL SELECT 'subject_grades.term_id', count(*) FROM subject_grades g LEFT JOIN terms t ON t.id = g.term_id WHERE g.term_id IS NOT NULL AND t.id IS NULL
UNION ALL SELECT 'report_cards.student_id', count(*) FROM report_cards r LEFT JOIN students s ON s.id = r.student_id WHERE r.student_id IS NOT NULL AND s.id IS NULL
UNION ALL SELECT 'report_cards.session_id', count(*) FROM report_cards r LEFT JOIN academic_sessions x ON x.id = r.session_id WHERE r.session_id IS NOT NULL AND x.id IS NULL
UNION ALL SELECT 'report_cards.term_id', count(*) FROM report_cards r LEFT JOIN terms t ON t.id = r.term_id WHERE r.term_id IS NOT NULL AND t.id IS NULL
UNION ALL SELECT 'report_cards.class_id', count(*) FROM report_cards r LEFT JOIN classes c ON c.id = r.class_id WHERE r.class_id IS NOT NULL AND c.id IS NULL
UNION ALL SELECT 'student_fees.student_id', count(*) FROM student_fees f LEFT JOIN students s ON s.id = f.student_id WHERE f.student_id IS NOT NULL AND s.id IS NULL
UNION ALL SELECT 'student_fees.session_id', count(*) FROM student_fees f LEFT JOIN academic_sessions x ON x.id = f.session_id WHERE f.session_id IS NOT NULL AND x.id IS NULL
UNION ALL SELECT 'payments.student_id', count(*) FROM payments p LEFT JOIN students s ON s.id = p.student_id WHERE p.student_id IS NOT NULL AND s.id IS NULL
UNION ALL SELECT 'attendance_records.student_id', count(*) FROM attendance_records a LEFT JOIN students s ON s.id = a.student_id WHERE a.student_id IS NOT NULL AND s.id IS NULL
UNION ALL SELECT 'attendance_records.class_id', count(*) FROM attendance_records a LEFT JOIN classes c ON c.id = a.class_id WHERE a.class_id IS NOT NULL AND c.id IS NULL
UNION ALL SELECT 'attendance_records.session_id', count(*) FROM attendance_records a LEFT JOIN academic_sessions x ON x.id = a.session_id WHERE a.session_id IS NOT NULL AND x.id IS NULL
UNION ALL SELECT 'attendance_records.term_id', count(*) FROM attendance_records a LEFT JOIN terms t ON t.id = a.term_id WHERE a.term_id IS NOT NULL AND t.id IS NULL
UNION ALL SELECT 'attendance_summaries.student_id', count(*) FROM attendance_summaries a LEFT JOIN students s ON s.id = a.student_id WHERE a.student_id IS NOT NULL AND s.id IS NULL
UNION ALL SELECT 'attendance_summaries.session_id', count(*) FROM attendance_summaries a LEFT JOIN academic_sessions x ON x.id = a.session_id WHERE a.session_id IS NOT NULL AND x.id IS NULL
UNION ALL SELECT 'attendance_summaries.term_id', count(*) FROM attendance_summaries a LEFT JOIN terms t ON t.id = a.term_id WHERE a.term_id IS NOT NULL AND t.id IS NULL
UNION ALL SELECT 'leave_requests.student_id', count(*) FROM leave_requests l LEFT JOIN students s ON s.id = l.student_id WHERE l.student_id IS NOT NULL AND s.id IS NULL
UNION ALL SELECT 'class_subjects.class_id', count(*) FROM class_subjects c LEFT JOIN classes x ON x.id = c.class_id WHERE c.class_id IS NOT NULL AND x.id IS NULL
UNION ALL SELECT 'class_subjects.subject_id', count(*) FROM class_subjects c LEFT JOIN subjects x ON x.id = c.subject_id WHERE c.subject_id IS NOT NULL AND x.id IS NULL
UNION ALL SELECT 'class_subjects.session_id', count(*) FROM class_subjects c LEFT JOIN academic_sessions x ON x.id = c.session_id WHERE c.session_id IS NOT NULL AND x.id IS NULL
UNION ALL SELECT 'teacher_class_assignments.teacher_id', count(*) FROM teacher_class_assignments a LEFT JOIN teachers t ON t.id = a.teacher_id WHERE a.teacher_id IS NOT NULL AND t.id IS NULL
UNION ALL SELECT 'teacher_class_assignments.class_id', count(*) FROM teacher_class_assignments a LEFT JOIN classes c ON c.id = a.class_id WHERE a.class_id IS NOT NULL AND c.id IS NULL
UNION ALL SELECT 'teacher_class_assignments.subject_id', count(*) FROM teacher_class_assignments a LEFT JOIN subjects s ON s.id = a.subject_id WHERE a.subject_id IS NOT NULL AND s.id IS NULL
UNION ALL SELECT 'teacher_class_assignments.session_id', count(*) FROM teacher_class_assignments a LEFT JOIN academic_sessions x ON x.id = a.session_id WHERE a.session_id IS NOT NULL AND x.id IS NULL
UNION ALL SELECT 'student_remarks.student_id', count(*) FROM student_remarks r LEFT JOIN students s ON s.id = r.student_id WHERE r.student_id IS NOT NULL AND s.id IS NULL
UNION ALL SELECT 'student_remarks.class_id', count(*) FROM student_remarks r LEFT JOIN classes c ON c.id = r.class_id WHERE r.class_id IS NOT NULL AND c.id IS NULL
UNION ALL SELECT 'student_remarks.session_id', count(*) FROM student_remarks r LEFT JOIN academic_sessions x ON x.id = r.session_id WHERE r.session_id IS NOT NULL AND x.id IS NULL
UNION ALL SELECT 'student_remarks.term_id', count(*) FROM student_remarks r LEFT JOIN terms t ON t.id = r.term_id WHERE r.term_id IS NOT NULL AND t.id IS NULL
UNION ALL SELECT 'student_remarks.form_teacher_id', count(*) FROM student_remarks r LEFT JOIN teachers t ON t.id = r.form_teacher_id WHERE r.form_teacher_id IS NOT NULL AND t.id IS NULL
UNION ALL SELECT 'student_skill_ratings.student_id', count(*) FROM student_skill_ratings r LEFT JOIN students s ON s.id = r.student_id WHERE r.student_id IS NOT NULL AND s.id IS NULL
UNION ALL SELECT 'student_skill_ratings.session_id', count(*) FROM student_skill_ratings r LEFT JOIN academic_sessions x ON x.id = r.session_id WHERE r.session_id IS NOT NULL AND x.id IS NULL
UNION ALL SELECT 'student_skill_ratings.term_id', count(*) FROM student_skill_ratings r LEFT JOIN terms t ON t.id = r.term_id WHERE r.term_id IS NOT NULL AND t.id IS NULL
UNION ALL SELECT 'student_skill_ratings.rated_by', count(*) FROM student_skill_ratings r LEFT JOIN teachers t ON t.id = r.rated_by WHERE r.rated_by IS NOT NULL AND t.id IS NULL
ORDER BY 1;
