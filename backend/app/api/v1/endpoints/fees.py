"""
Fee Management API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
import random
import string

from app.core.database import get_supabase
from app.core.security import get_current_user
from app.models.fees import (
    FeeCategory, FeeCategoryCreate, FeeCategoryUpdate,
    FeeStructure, FeeStructureCreate, FeeStructureUpdate,
    StudentFee, StudentFeeCreate, StudentFeeUpdate, StudentFeeWaiver,
    Payment, PaymentCreate, PaymentUpdate,
    PaymentAllocation, PaymentAllocationCreate,
    PaymentPlan, PaymentPlanCreate, PaymentPlanUpdate,
    PaymentInstallment,
    Receipt, ReceiptGenerate,
    FeeAnalytics, StudentFeesSummary
)

router = APIRouter()


# ============================================
# FEE CATEGORIES
# ============================================

@router.get("/categories", response_model=List[FeeCategory])
async def get_fee_categories(
    is_active: Optional[bool] = None,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Get all fee categories"""
    
    query = db.table("fee_categories").select("*").eq(
        "organization_id", current_user["school_id"]
    )
    
    if is_active is not None:
        query = query.eq("is_active", is_active)
    
    query = query.order("display_order")
    response = query.execute()
    
    return response.data


@router.post("/categories", response_model=FeeCategory, status_code=status.HTTP_201_CREATED)
async def create_fee_category(
    data: FeeCategoryCreate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Create new fee category (admin only)"""
    
    if current_user["role"] not in ["admin", "bursar"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and bursars can create fee categories"
        )
    
    category_data = data.model_dump(mode="json")
    category_data["organization_id"] = current_user["school_id"]
    
    response = db.table("fee_categories").insert(category_data).execute()
    
    return response.data[0]


# ============================================
# FEE STRUCTURES
# ============================================

@router.get("/structures", response_model=List[FeeStructure])
async def get_fee_structures(
    session_id: Optional[str] = None,
    class_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Get fee structures"""
    
    query = db.table("fee_structures").select(
        "*, fee_categories(name), classes(name)"
    ).eq("organization_id", current_user["school_id"])
    
    if session_id:
        query = query.eq("session_id", session_id)
    if class_id:
        query = query.eq("class_id", class_id)
    if is_active is not None:
        query = query.eq("is_active", is_active)
    
    response = query.execute()
    
    # Enrich data
    enriched_data = []
    for item in response.data:
        enriched_item = {**item}
        if "fee_categories" in item and item["fee_categories"]:
            enriched_item["category_name"] = item["fee_categories"]["name"]
        if "classes" in item and item["classes"]:
            enriched_item["class_name"] = item["classes"]["name"]
        enriched_data.append(enriched_item)
    
    return enriched_data


@router.post("/structures", response_model=FeeStructure, status_code=status.HTTP_201_CREATED)
async def create_fee_structure(
    data: FeeStructureCreate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Create new fee structure (admin only)"""
    
    if current_user["role"] not in ["admin", "bursar"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and bursars can create fee structures"
        )
    
    structure_data = data.model_dump(mode="json")
    structure_data["organization_id"] = current_user["school_id"]
    
    response = db.table("fee_structures").insert(structure_data).execute()
    
    return response.data[0]


@router.put("/structures/{structure_id}", response_model=FeeStructure)
async def update_fee_structure(
    structure_id: str,
    data: FeeStructureUpdate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Update fee structure (admin only)"""
    
    if current_user["role"] not in ["admin", "bursar"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and bursars can update fee structures"
        )
    
    update_data = data.model_dump(mode="json", exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow().isoformat()

    response = db.table("fee_structures").update(update_data).eq(
        "id", structure_id
    ).eq("organization_id", current_user["school_id"]).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fee structure not found"
        )
    
    return response.data[0]


# ============================================
# STUDENT FEES
# ============================================

@router.get("/student-fees", response_model=List[StudentFee])
async def get_student_fees(
    student_id: Optional[str] = None,
    session_id: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Get student fees"""
    
    query = db.table("student_fees").select(
        "*, students(admission_number, first_name, last_name), "
        "fee_structures(fee_categories(name))"
    ).eq("organization_id", current_user["school_id"])
    
    if student_id:
        query = query.eq("student_id", student_id)
    if session_id:
        query = query.eq("session_id", session_id)
    if status_filter:
        query = query.eq("status", status_filter)
    
    response = query.execute()
    
    # Enrich data
    enriched_data = []
    for item in response.data:
        enriched_item = {**item}
        if "students" in item and item["students"]:
            student = item["students"]
            enriched_item["student_name"] = f"{student['first_name']} {student['last_name']}"
            enriched_item["student_admission_number"] = student["admission_number"]
        if "fee_structures" in item and item["fee_structures"]:
            if "fee_categories" in item["fee_structures"]:
                enriched_item["category_name"] = item["fee_structures"]["fee_categories"]["name"]
        enriched_data.append(enriched_item)
    
    return enriched_data


@router.post("/student-fees", response_model=StudentFee, status_code=status.HTTP_201_CREATED)
async def assign_fee_to_student(
    data: StudentFeeCreate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Assign fee to student (admin only)"""
    
    if current_user["role"] not in ["admin", "bursar"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and bursars can assign fees"
        )
    
    fee_data = data.model_dump(mode="json")
    fee_data["organization_id"] = current_user["school_id"]
    fee_data["amount_paid"] = 0.00
    fee_data["balance"] = fee_data["final_amount"]
    fee_data["status"] = "pending"
    
    response = db.table("student_fees").insert(fee_data).execute()
    
    return response.data[0]


@router.post("/student-fees/bulk-assign")
async def bulk_assign_fees(
    session_id: str,
    class_id: str,
    fee_structure_ids: List[str],
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Assign fees to all students in a class"""
    
    if current_user["role"] not in ["admin", "bursar"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and bursars can assign fees"
        )
    
    # Get students in class
    enrollments = db.table("enrollments").select("student_id").eq(
        "class_id", class_id
    ).execute()
    
    if not enrollments.data:
        return {"message": "No students found in class", "fees_assigned": 0}
    
    student_ids = [e["student_id"] for e in enrollments.data]
    
    # Get fee structures
    structures = db.table("fee_structures").select("*").in_(
        "id", fee_structure_ids
    ).execute()
    
    # Create student fees
    fees_to_insert = []
    for student_id in student_ids:
        for structure in structures.data:
            fee_data = {
                "organization_id": current_user["school_id"],
                "student_id": student_id,
                "fee_structure_id": structure["id"],
                "session_id": session_id,
                "amount": structure["amount"],
                "discount_amount": Decimal("0.00"),
                "final_amount": structure["amount"],
                "amount_paid": Decimal("0.00"),
                "balance": structure["amount"],
                "status": "pending",
                "due_date": structure.get("due_date")
            }
            fees_to_insert.append(fee_data)
    
    response = db.table("student_fees").insert(fees_to_insert).execute()
    
    return {
        "message": f"Successfully assigned fees to {len(student_ids)} students",
        "fees_assigned": len(response.data)
    }


@router.post("/student-fees/{fee_id}/waive")
async def waive_student_fee(
    fee_id: str,
    data: StudentFeeWaiver,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Waive a student fee (admin only)"""
    
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can waive fees"
        )
    
    update_data = {
        "status": "waived",
        "is_waived": True,
        "waiver_reason": data.waiver_reason,
        "waived_by": current_user["id"],
        "waived_at": datetime.utcnow().isoformat(),
        "balance": Decimal("0.00")
    }
    
    response = db.table("student_fees").update(update_data).eq(
        "id", fee_id
    ).eq("organization_id", current_user["school_id"]).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student fee not found"
        )
    
    return response.data[0]


# ============================================
# PAYMENTS
# ============================================

def generate_receipt_number():
    """Generate unique receipt number"""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_part = ''.join(random.choices(string.digits, k=4))
    return f"REC-{timestamp}-{random_part}"


@router.get("/payments", response_model=List[Payment])
async def get_payments(
    student_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Get payments"""
    
    query = db.table("payments").select(
        "*, students(admission_number, first_name, last_name)"
    ).eq("organization_id", current_user["school_id"])
    
    if student_id:
        query = query.eq("student_id", student_id)
    if start_date:
        query = query.gte("payment_date", start_date.isoformat())
    if end_date:
        query = query.lte("payment_date", end_date.isoformat())
    if status_filter:
        query = query.eq("status", status_filter)
    
    query = query.order("payment_date", desc=True)
    response = query.execute()
    
    # Enrich data
    enriched_data = []
    for item in response.data:
        enriched_item = {**item}
        if "students" in item and item["students"]:
            student = item["students"]
            enriched_item["student_name"] = f"{student['first_name']} {student['last_name']}"
            enriched_item["student_admission_number"] = student["admission_number"]
        enriched_data.append(enriched_item)
    
    return enriched_data


@router.post("/payments", response_model=Payment, status_code=status.HTTP_201_CREATED)
async def record_payment(
    data: PaymentCreate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Record new payment"""
    
    if current_user["role"] not in ["admin", "bursar"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and bursars can record payments"
        )
    
    # Generate receipt number
    receipt_number = generate_receipt_number()
    
    payment_data = data.model_dump(mode="json", exclude={"fee_allocations"})
    payment_data["organization_id"] = current_user["school_id"]
    payment_data["receipt_number"] = receipt_number
    payment_data["status"] = "confirmed"
    payment_data["recorded_by"] = current_user["id"]
    payment_data["recorded_at"] = datetime.utcnow().isoformat()
    
    # Insert payment
    payment_response = db.table("payments").insert(payment_data).execute()
    payment_id = payment_response.data[0]["id"]
    
    # Handle fee allocations
    if data.fee_allocations:
        allocations = []
        for allocation in data.fee_allocations:
            allocations.append({
                "payment_id": payment_id,
                "student_fee_id": allocation["student_fee_id"],
                "allocated_amount": allocation["allocated_amount"]
            })
        
        db.table("payment_allocations").insert(allocations).execute()
        
        # Update student fees
        for allocation in data.fee_allocations:
            student_fee = db.table("student_fees").select("*").eq(
                "id", allocation["student_fee_id"]
            ).execute()
            
            if student_fee.data:
                fee = student_fee.data[0]
                new_paid = float(fee["amount_paid"]) + float(allocation["allocated_amount"])
                new_balance = float(fee["final_amount"]) - new_paid
                
                # Determine status
                new_status = "paid" if new_balance <= 0 else "partial"
                
                db.table("student_fees").update({
                    "amount_paid": new_paid,
                    "balance": new_balance,
                    "status": new_status,
                    "paid_date": data.payment_date.isoformat() if new_balance <= 0 else None
                }).eq("id", allocation["student_fee_id"]).execute()
    
    # Generate receipt
    receipt_data = {
        "organization_id": current_user["school_id"],
        "payment_id": payment_id,
        "receipt_number": receipt_number,
        "receipt_date": data.payment_date.isoformat(),
        "generated_at": datetime.utcnow().isoformat()
    }
    db.table("receipts").insert(receipt_data).execute()
    
    return payment_response.data[0]


# ============================================
# ANALYTICS
# ============================================

@router.get("/analytics/financial")
async def get_financial_analytics(
    session_id: str,
    term_id: Optional[str] = None,
    class_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Get financial analytics"""
    
    query = db.table("student_fees").select("*").eq(
        "organization_id", current_user["school_id"]
    ).eq("session_id", session_id)
    
    if term_id:
        query = query.eq("term_id", term_id)
    
    response = query.execute()
    
    if not response.data:
        return {
            "total_expected": 0,
            "total_collected": 0,
            "total_outstanding": 0,
            "collection_rate": 0,
            "students_fully_paid": 0,
            "students_partial_payment": 0,
            "students_no_payment": 0,
            "total_students": 0
        }
    
    total_expected = sum(float(f["final_amount"]) for f in response.data)
    total_collected = sum(float(f["amount_paid"]) for f in response.data)
    total_outstanding = total_expected - total_collected
    collection_rate = (total_collected / total_expected * 100) if total_expected > 0 else 0
    
    # Student payment status
    student_fees = {}
    for fee in response.data:
        student_id = fee["student_id"]
        if student_id not in student_fees:
            student_fees[student_id] = {"expected": 0, "paid": 0}
        student_fees[student_id]["expected"] += float(fee["final_amount"])
        student_fees[student_id]["paid"] += float(fee["amount_paid"])
    
    students_fully_paid = sum(1 for s in student_fees.values() if s["paid"] >= s["expected"])
    students_partial_payment = sum(1 for s in student_fees.values() if 0 < s["paid"] < s["expected"])
    students_no_payment = sum(1 for s in student_fees.values() if s["paid"] == 0)
    
    return {
        "total_expected": total_expected,
        "total_collected": total_collected,
        "total_outstanding": total_outstanding,
        "collection_rate": collection_rate,
        "students_fully_paid": students_fully_paid,
        "students_partial_payment": students_partial_payment,
        "students_no_payment": students_no_payment,
        "total_students": len(student_fees)
    }


@router.get("/analytics/student/{student_id}")
async def get_student_fees_summary(
    student_id: str,
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Get fee summary for a student"""
    
    # Get student details
    student = db.table("students").select("first_name, last_name").eq(
        "id", student_id
    ).execute()
    
    if not student.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    student_data = student.data[0]
    student_name = f"{student_data['first_name']} {student_data['last_name']}"
    
    # Get fees
    fees = db.table("student_fees").select(
        "*, fee_structures(fee_categories(name))"
    ).eq("student_id", student_id).eq(
        "session_id", session_id
    ).execute()
    
    total_fees = sum(float(f["final_amount"]) for f in fees.data)
    total_paid = sum(float(f["amount_paid"]) for f in fees.data)
    total_outstanding = total_fees - total_paid
    
    return {
        "student_id": student_id,
        "student_name": student_name,
        "session_id": session_id,
        "total_fees": total_fees,
        "total_paid": total_paid,
        "total_outstanding": total_outstanding,
        "fees": fees.data
    }


@router.get("/receipts/{receipt_number}")
async def get_receipt(
    receipt_number: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Get receipt details"""
    
    response = db.table("receipts").select(
        "*, payments(*, students(first_name, last_name, admission_number))"
    ).eq("receipt_number", receipt_number).eq(
        "organization_id", current_user["school_id"]
    ).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt not found"
        )
    
    return response.data[0]
