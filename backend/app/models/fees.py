"""
Pydantic models for Fee Management System
"""

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from decimal import Decimal


# ============================================
# FEE CATEGORIES
# ============================================

class FeeCategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=50)
    description: Optional[str] = None
    is_mandatory: bool = True
    is_active: bool = True
    display_order: int = 0


class FeeCategoryCreate(FeeCategoryBase):
    pass


class FeeCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    is_mandatory: Optional[bool] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None


class FeeCategory(FeeCategoryBase):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================
# FEE STRUCTURES
# ============================================

class FeeStructureBase(BaseModel):
    fee_category_id: str
    session_id: str
    class_level: Optional[str] = None  # 'Primary', 'Junior', 'Senior'
    class_id: Optional[str] = None
    amount: Decimal = Field(..., ge=0)
    currency: str = Field(default="NGN", max_length=3)
    payment_frequency: str = Field(default="termly", pattern="^(termly|annually|monthly|one-time)$")
    due_date: Optional[date] = None
    has_early_payment_discount: bool = False
    early_payment_discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    early_payment_deadline: Optional[date] = None
    is_active: bool = True


class FeeStructureCreate(FeeStructureBase):
    pass


class FeeStructureUpdate(BaseModel):
    amount: Optional[Decimal] = Field(None, ge=0)
    due_date: Optional[date] = None
    has_early_payment_discount: Optional[bool] = None
    early_payment_discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    early_payment_deadline: Optional[date] = None
    is_active: Optional[bool] = None


class FeeStructure(FeeStructureBase):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime

    # Enriched fields
    category_name: Optional[str] = None
    class_name: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================
# STUDENT FEES
# ============================================

class StudentFeeBase(BaseModel):
    student_id: str
    fee_structure_id: str
    session_id: str
    term_id: Optional[str] = None
    amount: Decimal = Field(..., ge=0)
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    final_amount: Decimal = Field(..., ge=0)
    due_date: Optional[date] = None


class StudentFeeCreate(StudentFeeBase):
    pass


class StudentFeeUpdate(BaseModel):
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    final_amount: Optional[Decimal] = Field(None, ge=0)
    due_date: Optional[date] = None


class StudentFeeWaiver(BaseModel):
    waiver_reason: str


class StudentFee(StudentFeeBase):
    id: str
    organization_id: str
    amount_paid: Decimal = Field(default=Decimal("0.00"))
    balance: Decimal
    status: str  # pending, partial, paid, overdue, waived
    paid_date: Optional[date] = None
    is_waived: bool = False
    waiver_reason: Optional[str] = None
    waived_by: Optional[str] = None
    waived_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Enriched fields
    student_name: Optional[str] = None
    student_admission_number: Optional[str] = None
    category_name: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================
# PAYMENTS
# ============================================

class PaymentBase(BaseModel):
    student_id: str
    payment_date: date
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="NGN", max_length=3)
    payment_method: str = Field(..., pattern="^(cash|bank_transfer|card|cheque|online)$")
    reference_number: Optional[str] = None
    bank_name: Optional[str] = None
    payer_name: Optional[str] = None
    payer_phone: Optional[str] = None
    payer_email: Optional[str] = None
    notes: Optional[str] = None


class PaymentCreate(PaymentBase):
    fee_allocations: Optional[List[dict]] = None  # [{student_fee_id, allocated_amount}]


class PaymentUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(pending|confirmed|cancelled|refunded)$")
    notes: Optional[str] = None


class Payment(PaymentBase):
    id: str
    organization_id: str
    receipt_number: str
    status: str  # pending, confirmed, cancelled, refunded
    recorded_by: Optional[str] = None
    recorded_at: datetime
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Enriched fields
    student_name: Optional[str] = None
    student_admission_number: Optional[str] = None
    recorded_by_name: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================
# PAYMENT ALLOCATIONS
# ============================================

class PaymentAllocationBase(BaseModel):
    payment_id: str
    student_fee_id: str
    allocated_amount: Decimal = Field(..., gt=0)


class PaymentAllocationCreate(PaymentAllocationBase):
    pass


class PaymentAllocation(PaymentAllocationBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================
# PAYMENT PLANS
# ============================================

class PaymentPlanBase(BaseModel):
    student_id: str
    student_fee_id: str
    plan_name: Optional[str] = None
    total_amount: Decimal = Field(..., gt=0)
    number_of_installments: int = Field(..., gt=0)
    installment_amount: Decimal = Field(..., gt=0)
    start_date: date
    frequency: str = Field(default="monthly", pattern="^(weekly|monthly|custom)$")


class PaymentPlanCreate(PaymentPlanBase):
    pass


class PaymentPlanUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(active|completed|cancelled|defaulted)$")


class PaymentPlan(PaymentPlanBase):
    id: str
    organization_id: str
    status: str  # active, completed, cancelled, defaulted
    created_at: datetime
    updated_at: datetime

    # Enriched fields
    student_name: Optional[str] = None
    installments: Optional[List[dict]] = []

    class Config:
        from_attributes = True


# ============================================
# PAYMENT INSTALLMENTS
# ============================================

class PaymentInstallmentBase(BaseModel):
    payment_plan_id: str
    installment_number: int
    due_date: date
    amount: Decimal = Field(..., gt=0)


class PaymentInstallmentCreate(PaymentInstallmentBase):
    pass


class PaymentInstallment(PaymentInstallmentBase):
    id: str
    status: str  # pending, paid, overdue
    paid_date: Optional[date] = None
    payment_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================
# RECEIPTS
# ============================================

class ReceiptBase(BaseModel):
    payment_id: str
    receipt_date: date
    content: Optional[dict] = None


class ReceiptGenerate(BaseModel):
    """Request to generate receipt"""
    payment_id: str


class Receipt(ReceiptBase):
    id: str
    organization_id: str
    receipt_number: str
    pdf_url: Optional[str] = None
    generated_at: Optional[datetime] = None
    emailed_to: Optional[str] = None
    emailed_at: Optional[datetime] = None
    printed_at: Optional[datetime] = None
    printed_by: Optional[str] = None
    print_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================
# ANALYTICS
# ============================================

class FeeAnalytics(BaseModel):
    """Financial statistics"""
    total_expected: Decimal
    total_collected: Decimal
    total_outstanding: Decimal
    collection_rate: Decimal
    students_fully_paid: int
    students_partial_payment: int
    students_no_payment: int
    total_students: int


class StudentFeesSummary(BaseModel):
    """Summary of fees for a student"""
    student_id: str
    student_name: str
    session_id: str
    total_fees: Decimal
    total_paid: Decimal
    total_outstanding: Decimal
    fees: List[StudentFee]
