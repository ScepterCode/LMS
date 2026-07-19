-- =====================================================
-- Phase 3C: Fee Management Schema
-- Learnlyf
-- =====================================================

-- Fee Categories (Types of fees)
CREATE TABLE IF NOT EXISTS fee_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    name VARCHAR(100) NOT NULL, -- "Tuition", "Uniform", "Books", "Transport"
    code VARCHAR(50) NOT NULL,
    description TEXT,
    is_mandatory BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    display_order INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(organization_id, code)
);

-- Fee Structures (Fee amounts per category)
CREATE TABLE IF NOT EXISTS fee_structures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    fee_category_id UUID NOT NULL REFERENCES fee_categories(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
    
    -- Applicability
    class_level VARCHAR(20), -- 'Primary', 'Junior', 'Senior', or NULL for all
    class_id UUID REFERENCES classes(id) ON DELETE CASCADE, -- Specific class or NULL for level
    
    amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'NGN',
    
    -- Payment terms
    payment_frequency VARCHAR(20) DEFAULT 'termly', -- 'termly', 'annually', 'monthly', 'one-time'
    due_date DATE,
    
    -- Discounts
    has_early_payment_discount BOOLEAN DEFAULT false,
    early_payment_discount_percentage DECIMAL(5,2),
    early_payment_deadline DATE,
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_amount_positive CHECK (amount >= 0),
    CONSTRAINT check_discount CHECK (early_payment_discount_percentage >= 0 AND early_payment_discount_percentage <= 100)
);

-- Student Fee Assignments (Fees assigned to specific students)
CREATE TABLE IF NOT EXISTS student_fees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    fee_structure_id UUID NOT NULL REFERENCES fee_structures(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
    term_id UUID REFERENCES terms(id) ON DELETE CASCADE,
    
    -- Fee details
    amount DECIMAL(12,2) NOT NULL,
    discount_amount DECIMAL(12,2) DEFAULT 0.00,
    final_amount DECIMAL(12,2) NOT NULL, -- amount - discount
    
    -- Payment status
    amount_paid DECIMAL(12,2) DEFAULT 0.00,
    balance DECIMAL(12,2) NOT NULL, -- final_amount - amount_paid
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'partial', 'paid', 'overdue', 'waived'
    
    -- Dates
    due_date DATE,
    paid_date DATE,
    
    -- Waiver/Exemption
    is_waived BOOLEAN DEFAULT false,
    waiver_reason TEXT,
    waived_by UUID REFERENCES users(id) ON DELETE SET NULL,
    waived_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_fee_status CHECK (status IN ('pending', 'partial', 'paid', 'overdue', 'waived')),
    CONSTRAINT check_amounts_valid CHECK (amount >= 0 AND amount_paid >= 0 AND final_amount >= 0)
);

-- Payments (Payment records)
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    
    -- Payment details
    receipt_number VARCHAR(50) NOT NULL UNIQUE,
    payment_date DATE NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'NGN',
    
    -- Payment method
    payment_method VARCHAR(50) NOT NULL, -- 'cash', 'bank_transfer', 'card', 'cheque', 'online'
    reference_number VARCHAR(100), -- Bank transaction reference
    bank_name VARCHAR(100),
    
    -- Payer info
    payer_name VARCHAR(200),
    payer_phone VARCHAR(20),
    payer_email VARCHAR(200),
    
    -- Status
    status VARCHAR(20) DEFAULT 'confirmed', -- 'pending', 'confirmed', 'cancelled', 'refunded'
    notes TEXT,
    
    -- Recorded by
    recorded_by UUID REFERENCES users(id) ON DELETE SET NULL,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Approval
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_payment_amount CHECK (amount > 0),
    CONSTRAINT check_payment_status CHECK (status IN ('pending', 'confirmed', 'cancelled', 'refunded')),
    CONSTRAINT check_payment_method CHECK (payment_method IN ('cash', 'bank_transfer', 'card', 'cheque', 'online'))
);

-- Payment Allocations (Link payments to specific fees)
CREATE TABLE IF NOT EXISTS payment_allocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
    student_fee_id UUID NOT NULL REFERENCES student_fees(id) ON DELETE CASCADE,
    
    allocated_amount DECIMAL(12,2) NOT NULL,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_allocated_amount CHECK (allocated_amount > 0)
);

-- Payment Plans (Installment plans)
CREATE TABLE IF NOT EXISTS payment_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    student_fee_id UUID NOT NULL REFERENCES student_fees(id) ON DELETE CASCADE,
    
    plan_name VARCHAR(100),
    total_amount DECIMAL(12,2) NOT NULL,
    number_of_installments INTEGER NOT NULL,
    installment_amount DECIMAL(12,2) NOT NULL,
    
    start_date DATE NOT NULL,
    frequency VARCHAR(20) DEFAULT 'monthly', -- 'weekly', 'monthly', 'custom'
    
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'completed', 'cancelled', 'defaulted'
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_installments CHECK (number_of_installments > 0),
    CONSTRAINT check_plan_status CHECK (status IN ('active', 'completed', 'cancelled', 'defaulted'))
);

-- Payment Plan Installments
CREATE TABLE IF NOT EXISTS payment_installments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_plan_id UUID NOT NULL REFERENCES payment_plans(id) ON DELETE CASCADE,
    
    installment_number INTEGER NOT NULL,
    due_date DATE NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'paid', 'overdue'
    paid_date DATE,
    payment_id UUID REFERENCES payments(id) ON DELETE SET NULL,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_installment_status CHECK (status IN ('pending', 'paid', 'overdue')),
    UNIQUE(payment_plan_id, installment_number)
);

-- Receipts (Auto-generated or manual receipts)
CREATE TABLE IF NOT EXISTS receipts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    payment_id UUID NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
    
    receipt_number VARCHAR(50) NOT NULL UNIQUE,
    receipt_date DATE NOT NULL,
    
    -- Receipt content (JSON for flexibility)
    content JSONB,
    
    -- PDF generation
    pdf_url TEXT,
    generated_at TIMESTAMP WITH TIME ZONE,
    
    -- Email tracking
    emailed_to VARCHAR(200),
    emailed_at TIMESTAMP WITH TIME ZONE,
    
    -- Print tracking
    printed_at TIMESTAMP WITH TIME ZONE,
    printed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    print_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Fee Reminders (Payment reminder tracking)
CREATE TABLE IF NOT EXISTS fee_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    student_fee_id UUID NOT NULL REFERENCES student_fees(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    
    reminder_type VARCHAR(20) NOT NULL, -- 'email', 'sms', 'notification'
    reminder_date DATE NOT NULL,
    
    message_sent BOOLEAN DEFAULT false,
    sent_at TIMESTAMP WITH TIME ZONE,
    
    recipient VARCHAR(200), -- Email or phone number
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_reminder_type CHECK (reminder_type IN ('email', 'sms', 'notification'))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_fee_structures_org ON fee_structures(organization_id);
CREATE INDEX IF NOT EXISTS idx_fee_structures_session ON fee_structures(session_id);
CREATE INDEX IF NOT EXISTS idx_fee_structures_class ON fee_structures(class_id);

CREATE INDEX IF NOT EXISTS idx_student_fees_student ON student_fees(student_id);
CREATE INDEX IF NOT EXISTS idx_student_fees_status ON student_fees(status);
CREATE INDEX IF NOT EXISTS idx_student_fees_session ON student_fees(session_id, term_id);

CREATE INDEX IF NOT EXISTS idx_payments_student ON payments(student_id);
CREATE INDEX IF NOT EXISTS idx_payments_date ON payments(payment_date);
CREATE INDEX IF NOT EXISTS idx_payments_receipt ON payments(receipt_number);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);

CREATE INDEX IF NOT EXISTS idx_payment_allocations_payment ON payment_allocations(payment_id);
CREATE INDEX IF NOT EXISTS idx_payment_allocations_fee ON payment_allocations(student_fee_id);

CREATE INDEX IF NOT EXISTS idx_payment_plans_student ON payment_plans(student_id);
CREATE INDEX IF NOT EXISTS idx_payment_plans_status ON payment_plans(status);

CREATE INDEX IF NOT EXISTS idx_receipts_payment ON receipts(payment_id);
CREATE INDEX IF NOT EXISTS idx_receipts_number ON receipts(receipt_number);

-- Comments
COMMENT ON TABLE fee_categories IS 'Types of fees (tuition, uniform, etc.)';
COMMENT ON TABLE fee_structures IS 'Fee amounts per category and class';
COMMENT ON TABLE student_fees IS 'Fees assigned to specific students';
COMMENT ON TABLE payments IS 'Payment records';
COMMENT ON TABLE payment_allocations IS 'Link payments to specific fees';
COMMENT ON TABLE payment_plans IS 'Installment payment plans';
COMMENT ON TABLE payment_installments IS 'Individual installment records';
COMMENT ON TABLE receipts IS 'Payment receipts';
COMMENT ON TABLE fee_reminders IS 'Payment reminder tracking';
