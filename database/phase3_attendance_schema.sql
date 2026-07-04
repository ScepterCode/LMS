-- =====================================================
-- Phase 3B: Attendance Management Schema
-- Nigerian School Management System
-- =====================================================

-- Daily Attendance Records
CREATE TABLE IF NOT EXISTS attendance_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
    term_id UUID NOT NULL REFERENCES terms(id) ON DELETE CASCADE,
    
    attendance_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL, -- 'present', 'absent', 'late', 'excused'
    
    -- Time tracking
    check_in_time TIME,
    check_out_time TIME,
    minutes_late INTEGER DEFAULT 0,
    
    -- Additional info
    reason TEXT, -- Reason for absence/lateness
    notes TEXT,
    
    -- Marked by
    marked_by UUID REFERENCES users(id) ON DELETE SET NULL,
    marked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(student_id, attendance_date),
    CONSTRAINT check_attendance_status CHECK (status IN ('present', 'absent', 'late', 'excused'))
);

-- Attendance Summaries (Aggregated stats per student per term)
CREATE TABLE IF NOT EXISTS attendance_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
    term_id UUID NOT NULL REFERENCES terms(id) ON DELETE CASCADE,
    
    -- Counts
    days_present INTEGER DEFAULT 0,
    days_absent INTEGER DEFAULT 0,
    days_late INTEGER DEFAULT 0,
    days_excused INTEGER DEFAULT 0,
    total_school_days INTEGER DEFAULT 0,
    
    -- Calculated percentages
    attendance_percentage DECIMAL(5,2), -- (present + late) / total * 100
    punctuality_percentage DECIMAL(5,2), -- present / (present + late) * 100
    
    -- Last update
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(student_id, term_id, session_id)
);

-- Leave Requests (Student absence requests from parents)
CREATE TABLE IF NOT EXISTS leave_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    leave_type VARCHAR(50) NOT NULL, -- 'sick', 'family', 'emergency', 'other'
    reason TEXT NOT NULL,
    
    -- Supporting documents
    attachment_url TEXT,
    
    -- Approval workflow
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_at TIMESTAMP WITH TIME ZONE,
    rejection_reason TEXT,
    
    -- Submitted by (parent or guardian)
    submitted_by UUID REFERENCES users(id) ON DELETE SET NULL,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_leave_dates CHECK (end_date >= start_date),
    CONSTRAINT check_leave_status CHECK (status IN ('pending', 'approved', 'rejected')),
    CONSTRAINT check_leave_type CHECK (leave_type IN ('sick', 'family', 'emergency', 'other'))
);

-- Attendance Settings (School-wide attendance configuration)
CREATE TABLE IF NOT EXISTS attendance_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- School timing
    school_start_time TIME NOT NULL DEFAULT '08:00:00',
    school_end_time TIME NOT NULL DEFAULT '14:00:00',
    late_threshold_minutes INTEGER DEFAULT 15, -- Minutes after start time to mark as late
    
    -- Auto-absence settings
    auto_mark_absent BOOLEAN DEFAULT false, -- Auto mark as absent if not marked
    auto_mark_time TIME, -- Time to run auto-marking
    
    -- Notification settings
    notify_parents_on_absence BOOLEAN DEFAULT true,
    notify_parents_on_late BOOLEAN DEFAULT false,
    absence_threshold_notify INTEGER DEFAULT 3, -- Notify after N consecutive absences
    
    -- Working days
    working_days JSONB DEFAULT '["monday","tuesday","wednesday","thursday","friday"]'::jsonb,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(organization_id)
);

-- Holiday Calendar (School holidays and non-working days)
CREATE TABLE IF NOT EXISTS holidays (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    session_id UUID REFERENCES academic_sessions(id) ON DELETE CASCADE,
    
    holiday_name VARCHAR(200) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    holiday_type VARCHAR(50) DEFAULT 'public', -- 'public', 'school', 'term_break'
    description TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_holiday_dates CHECK (end_date >= start_date),
    CONSTRAINT check_holiday_type CHECK (holiday_type IN ('public', 'school', 'term_break'))
);

-- Teacher Attendance (Optional - for staff attendance tracking)
CREATE TABLE IF NOT EXISTS teacher_attendance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    teacher_id UUID NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    
    attendance_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL, -- 'present', 'absent', 'late', 'on_leave'
    
    check_in_time TIME,
    check_out_time TIME,
    hours_worked DECIMAL(4,2),
    
    reason TEXT,
    notes TEXT,
    
    marked_by UUID REFERENCES users(id) ON DELETE SET NULL,
    marked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(teacher_id, attendance_date),
    CONSTRAINT check_teacher_status CHECK (status IN ('present', 'absent', 'late', 'on_leave'))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance_records(student_id);
CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance_records(attendance_date);
CREATE INDEX IF NOT EXISTS idx_attendance_class ON attendance_records(class_id);
CREATE INDEX IF NOT EXISTS idx_attendance_org_date ON attendance_records(organization_id, attendance_date);
CREATE INDEX IF NOT EXISTS idx_attendance_term ON attendance_records(term_id, session_id);

CREATE INDEX IF NOT EXISTS idx_attendance_summary_student ON attendance_summaries(student_id);
CREATE INDEX IF NOT EXISTS idx_attendance_summary_term ON attendance_summaries(term_id, session_id);

CREATE INDEX IF NOT EXISTS idx_leave_requests_student ON leave_requests(student_id);
CREATE INDEX IF NOT EXISTS idx_leave_requests_status ON leave_requests(status);
CREATE INDEX IF NOT EXISTS idx_leave_requests_dates ON leave_requests(start_date, end_date);

CREATE INDEX IF NOT EXISTS idx_holidays_org ON holidays(organization_id);
CREATE INDEX IF NOT EXISTS idx_holidays_dates ON holidays(start_date, end_date);

CREATE INDEX IF NOT EXISTS idx_teacher_attendance_teacher ON teacher_attendance(teacher_id);
CREATE INDEX IF NOT EXISTS idx_teacher_attendance_date ON teacher_attendance(attendance_date);

-- Comments
COMMENT ON TABLE attendance_records IS 'Daily student attendance tracking';
COMMENT ON TABLE attendance_summaries IS 'Aggregated attendance statistics per term';
COMMENT ON TABLE leave_requests IS 'Student leave/absence requests from parents';
COMMENT ON TABLE attendance_settings IS 'School-wide attendance configuration';
COMMENT ON TABLE holidays IS 'School holidays and non-working days';
COMMENT ON TABLE teacher_attendance IS 'Teacher/staff attendance tracking';
