"""
Fee Management API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, date
import random
import string

from app.core.database import get_supabase
from app.core.security import get_current_user
from app.core.permissions import PermissionChecker
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


def _sweep_overdue_fees(db, organization_id: str) -> None:
    """Flip pending/partial student_fees whose due_date has passed to
    'overdue'. There's no background scheduler in this deployment, so this
    runs as a scoped, idempotent sweep on every read instead - it only
    touches rows in the caller's own organization that are already
    unpaid and past due, matching the same transition record_payment
    would eventually make anyway."""
    today = date.today().isoformat()
    db.table("student_fees").update({"status": "overdue"}).eq(
        "organization_id", organization_id
    ).lt("due_date", today).in_("status", ["pending", "partial"]).execute()


# ============================================
# FEE CATEGORIES
# ============================================

@router.get("/categories", response_model=List[FeeCategory])
def get_fee_categories(
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
def create_fee_category(
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


@router.put("/categories/{category_id}", response_model=FeeCategory)
def update_fee_category(
    category_id: str,
    data: FeeCategoryUpdate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Update a fee category (admin/bursar only)"""

    if current_user["role"] not in ["admin", "bursar"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and bursars can update fee categories"
        )

    update_data = data.model_dump(mode="json", exclude_unset=True)
    if not update_data:
        existing = db.table("fee_categories").select("*").eq("id", category_id).eq(
            "organization_id", current_user["school_id"]
        ).execute()
        if not existing.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fee category not found")
        return existing.data[0]

    update_data["updated_at"] = datetime.utcnow().isoformat()

    response = db.table("fee_categories").update(update_data).eq(
        "id", category_id
    ).eq("organization_id", current_user["school_id"]).execute()

    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fee category not found")

    return response.data[0]


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fee_category(
    category_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Delete a fee category (admin/bursar only). Blocked if any fee
    structure still references it - deleting the category out from under
    an in-use structure would silently orphan every student fee built on it."""

    if current_user["role"] not in ["admin", "bursar"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and bursars can delete fee categories"
        )

    existing = db.table("fee_categories").select("id").eq("id", category_id).eq(
        "organization_id", current_user["school_id"]
    ).execute()
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fee category not found")

    in_use = db.table("fee_structures").select("id").eq("fee_category_id", category_id).execute()
    if in_use.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete: {len(in_use.data)} fee structure(s) still use this category. "
                   "Deactivate it instead, or delete those structures first."
        )

    db.table("fee_categories").delete().eq("id", category_id).eq(
        "organization_id", current_user["school_id"]
    ).execute()


# ============================================
# FEE STRUCTURES
# ============================================

@router.get("/structures", response_model=List[FeeStructure])
def get_fee_structures(
    session_id: Optional[str] = None,
    class_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Get fee structures"""

    query = db.table("fee_structures").select("*").eq("organization_id", current_user["school_id"])

    if session_id:
        query = query.eq("session_id", session_id)
    if class_id:
        query = query.eq("class_id", class_id)
    if is_active is not None:
        query = query.eq("is_active", is_active)

    response = query.execute()

    # Batch-fetch category/class names manually rather than via a PostgREST
    # embed join - fee_structures.class_id/session_id aren't backed by a DB
    # foreign key (even though the app-level checks on create enforce it),
    # so an embed join 500s with PGRST200. This also degrades gracefully if
    # a row ever points at a deleted class instead of failing the request.
    category_ids = list({item["fee_category_id"] for item in response.data if item.get("fee_category_id")})
    class_ids = list({item["class_id"] for item in response.data if item.get("class_id")})
    category_names: dict = {}
    class_names: dict = {}
    if category_ids:
        cats = db.table("fee_categories").select("id, name").in_("id", category_ids).execute()
        category_names = {row["id"]: row["name"] for row in (cats.data or [])}
    if class_ids:
        clss = db.table("classes").select("id, name").in_("id", class_ids).execute()
        class_names = {row["id"]: row["name"] for row in (clss.data or [])}

    enriched_data = []
    for item in response.data:
        enriched_item = {**item}
        enriched_item["category_name"] = category_names.get(item.get("fee_category_id"))
        enriched_item["class_name"] = class_names.get(item.get("class_id"))
        enriched_data.append(enriched_item)

    return enriched_data


@router.post("/structures", response_model=FeeStructure, status_code=status.HTTP_201_CREATED)
def create_fee_structure(
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
def update_fee_structure(
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


@router.delete("/structures/{structure_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fee_structure(
    structure_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Delete a fee structure (admin/bursar only). Blocked if any student
    has already been assigned a fee from it - those student_fees rows
    would otherwise point at a structure_id that no longer exists."""

    if current_user["role"] not in ["admin", "bursar"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and bursars can delete fee structures"
        )

    existing = db.table("fee_structures").select("id").eq("id", structure_id).eq(
        "organization_id", current_user["school_id"]
    ).execute()
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fee structure not found")

    in_use = db.table("student_fees").select("id").eq("fee_structure_id", structure_id).execute()
    if in_use.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete: {len(in_use.data)} student(s) already have a fee assigned from this "
                   "structure. Deactivate it instead."
        )

    db.table("fee_structures").delete().eq("id", structure_id).eq(
        "organization_id", current_user["school_id"]
    ).execute()


@router.get("/structures/{structure_id}/detail")
def get_fee_structure_detail(
    structure_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """One fee structure plus the students it's assigned to and collection
    totals. Read-only; admin/bursar only (same as the school-wide
    financial analytics)."""

    if current_user["role"] not in ["admin", "system_admin", "bursar"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and bursars can view fee structure details"
        )

    structure_resp = db.table("fee_structures").select("*").eq(
        "id", structure_id
    ).eq("organization_id", current_user["school_id"]).execute()
    if not structure_resp.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fee structure not found")
    structure = structure_resp.data[0]

    # Enrich category / class names (same manual-lookup approach as the list).
    if structure.get("fee_category_id"):
        cat = db.table("fee_categories").select("name").eq(
            "id", structure["fee_category_id"]
        ).eq("organization_id", current_user["school_id"]).execute()
        structure["category_name"] = cat.data[0]["name"] if cat.data else None
    if structure.get("class_id"):
        cls = db.table("classes").select("name").eq(
            "id", structure["class_id"]
        ).eq("organization_id", current_user["school_id"]).execute()
        structure["class_name"] = cls.data[0]["name"] if cls.data else None

    _sweep_overdue_fees(db, current_user["school_id"])

    fees_resp = db.table("student_fees").select(
        "id, student_id, final_amount, amount_paid, balance, status, is_waived, "
        "students(admission_number, first_name, last_name)"
    ).eq("organization_id", current_user["school_id"]).eq(
        "fee_structure_id", structure_id
    ).execute()
    rows = fees_resp.data or []

    students = []
    by_status: dict = {}
    total_expected = total_collected = total_outstanding = 0.0
    for r in rows:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
        total_expected += float(r["final_amount"] or 0)
        total_collected += float(r["amount_paid"] or 0)
        if not r.get("is_waived"):
            total_outstanding += float(r["balance"] or 0)
        s = r.get("students") or {}
        students.append({
            "student_fee_id": r["id"],
            "student_id": r["student_id"],
            "student_name": f"{s.get('first_name', '')} {s.get('last_name', '')}".strip() or None,
            "admission_number": s.get("admission_number"),
            "final_amount": float(r["final_amount"] or 0),
            "amount_paid": float(r["amount_paid"] or 0),
            "balance": float(r["balance"] or 0),
            "status": r["status"],
        })

    students.sort(key=lambda x: (x["student_name"] or "").lower())

    return {
        "structure": structure,
        "stats": {
            "student_count": len(rows),
            "total_expected": total_expected,
            "total_collected": total_collected,
            "total_outstanding": total_outstanding,
            "collection_rate": (total_collected / total_expected * 100) if total_expected > 0 else 0,
            "by_status": by_status,
        },
        "students": students,
    }


# ============================================
# STUDENT FEES
# ============================================

@router.get("/student-fees", response_model=List[StudentFee])
def get_student_fees(
    student_id: Optional[str] = None,
    session_id: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Get student fees"""

    if student_id:
        PermissionChecker.verify_can_view_student(
            current_user, student_id, db, extra_full_access_roles=("bursar",)
        )
    elif current_user["role"] not in ["admin", "system_admin", "bursar"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="student_id is required unless you are an admin or bursar"
        )

    _sweep_overdue_fees(db, current_user["school_id"])

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
def assign_fee_to_student(
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
def bulk_assign_fees(
    session_id: str,
    fee_structure_ids: List[str],
    class_id: Optional[str] = None,
    class_level: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Assign fees to all students in a class, or to every class at a
    given level (class_level was previously an orphaned FeeStructure field
    that nothing ever expanded - this is that expansion)."""

    if current_user["role"] not in ["admin", "bursar"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and bursars can assign fees"
        )

    if not class_id and not class_level:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either class_id or class_level is required"
        )

    if class_id:
        # Confirm the class belongs to the caller's org before trusting it -
        # class_id is caller-supplied and students aren't otherwise org-scoped
        # in this query.
        class_check = db.table("classes").select("id").eq("id", class_id).eq(
            "organization_id", current_user["school_id"]
        ).execute()
        if not class_check.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
        target_class_ids = [class_id]
    else:
        level_classes = db.table("classes").select("id").eq(
            "organization_id", current_user["school_id"]
        ).eq("level", class_level).execute()
        target_class_ids = [c["id"] for c in level_classes.data]
        if not target_class_ids:
            return {"message": f"No classes found at level {class_level}", "fees_assigned": 0}

    # Get students in the target class(es) (current_class_id is the source
    # of truth used everywhere else - "enrollments" is not a real table)
    enrollments = db.table("students").select("id").in_(
        "current_class_id", target_class_ids
    ).execute()

    if not enrollments.data:
        return {"message": "No students found in class", "fees_assigned": 0}

    student_ids = [e["id"] for e in enrollments.data]

    # Get fee structures (scoped to this org - fee_structure_ids are
    # caller-supplied)
    structures = db.table("fee_structures").select("*").in_(
        "id", fee_structure_ids
    ).eq("organization_id", current_user["school_id"]).execute()
    
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
                "discount_amount": 0.00,
                "final_amount": structure["amount"],
                "amount_paid": 0.00,
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
def waive_student_fee(
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
        "balance": 0.00
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
def get_payments(
    student_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Get payments"""

    if student_id:
        PermissionChecker.verify_can_view_student(
            current_user, student_id, db, extra_full_access_roles=("bursar",)
        )
    elif current_user["role"] not in ["admin", "system_admin", "bursar"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="student_id is required unless you are an admin or bursar"
        )

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
def record_payment(
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

    # Validate every fee being paid belongs to THIS organization BEFORE we
    # write anything. A payment must never read or modify another school's
    # student_fees; without this, an allocation referencing a foreign
    # student_fee_id silently overwrites that fee's balance/status.
    fees_by_id = {}
    if data.fee_allocations:
        requested_ids = list({a["student_fee_id"] for a in data.fee_allocations})
        owned = db.table("student_fees").select("*").in_(
            "id", requested_ids
        ).eq("organization_id", current_user["school_id"]).execute()
        fees_by_id = {f["id"]: f for f in (owned.data or [])}
        missing = [fid for fid in requested_ids if fid not in fees_by_id]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more fees could not be found for this organization"
            )

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

        # Update student fees (all validated as org-owned above)
        for allocation in data.fee_allocations:
            fee = fees_by_id[allocation["student_fee_id"]]
            new_paid = float(fee["amount_paid"]) + float(allocation["allocated_amount"])
            new_balance = float(fee["final_amount"]) - new_paid
            new_status = "paid" if new_balance <= 0 else "partial"
            db.table("student_fees").update({
                "amount_paid": new_paid,
                "balance": new_balance,
                "status": new_status,
                "paid_date": data.payment_date.isoformat() if new_balance <= 0 else None
            }).eq("id", allocation["student_fee_id"]).eq(
                "organization_id", current_user["school_id"]
            ).execute()
    
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


@router.put("/payments/{payment_id}", response_model=Payment)
def update_payment(
    payment_id: str,
    data: PaymentUpdate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Correct or void a payment (admin only).

    There was previously no way to fix a mis-recorded payment at all -
    the status column supported 'cancelled'/'refunded' but nothing ever
    set them. Moving status to cancelled/refunded reverses this payment's
    allocations against the student fees they were applied to (so the
    balance/status those fees show is accurate again). A payment that's
    already cancelled/refunded is terminal - record a new payment instead
    of trying to change it further, so the reversal above can never be
    applied twice.
    """

    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can correct or void payments"
        )

    existing = db.table("payments").select("*").eq("id", payment_id).eq(
        "organization_id", current_user["school_id"]
    ).execute()

    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    payment = existing.data[0]

    if payment["status"] in ("cancelled", "refunded"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This payment has already been voided and can't be changed further. Record a new payment instead."
        )

    update_data = data.model_dump(mode="json", exclude_unset=True)
    if not update_data:
        return payment

    voiding = update_data.get("status") in ("cancelled", "refunded")

    if voiding:
        allocations = db.table("payment_allocations").select("*").eq("payment_id", payment_id).execute()
        for allocation in allocations.data:
            fee = db.table("student_fees").select("*").eq("id", allocation["student_fee_id"]).execute()
            if not fee.data:
                continue
            student_fee = fee.data[0]
            new_paid = max(0.0, float(student_fee["amount_paid"]) - float(allocation["allocated_amount"]))
            new_balance = float(student_fee["final_amount"]) - new_paid
            new_status = "paid" if new_balance <= 0 else ("partial" if new_paid > 0 else "pending")

            db.table("student_fees").update({
                "amount_paid": new_paid,
                "balance": new_balance,
                "status": new_status,
                "paid_date": student_fee.get("paid_date") if new_balance <= 0 else None,
            }).eq("id", student_fee["id"]).execute()

    update_data["updated_at"] = datetime.utcnow().isoformat()

    response = db.table("payments").update(update_data).eq("id", payment_id).execute()

    return response.data[0]


# ============================================
# ANALYTICS
# ============================================

@router.get("/analytics/financial")
def get_financial_analytics(
    session_id: str,
    term_id: Optional[str] = None,
    class_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Get financial analytics"""

    if current_user["role"] not in ["admin", "system_admin", "bursar"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and bursars can view school-wide financial analytics"
        )

    _sweep_overdue_fees(db, current_user["school_id"])

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
            "students_overdue": 0,
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
    overdue_student_ids = {f["student_id"] for f in response.data if f["status"] == "overdue"}

    return {
        "total_expected": total_expected,
        "total_collected": total_collected,
        "total_outstanding": total_outstanding,
        "collection_rate": collection_rate,
        "students_fully_paid": students_fully_paid,
        "students_partial_payment": students_partial_payment,
        "students_no_payment": students_no_payment,
        "students_overdue": len(overdue_student_ids),
        "total_students": len(student_fees)
    }


@router.get("/analytics/student/{student_id}")
def get_student_fees_summary(
    student_id: str,
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Get fee summary for a student"""

    PermissionChecker.verify_can_view_student(
        current_user, student_id, db, extra_full_access_roles=("bursar",)
    )

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
def get_receipt(
    receipt_number: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Get receipt details"""

    response = db.table("receipts").select(
        "*, payments(*, students(id, first_name, last_name, admission_number))"
    ).eq("receipt_number", receipt_number).eq(
        "organization_id", current_user["school_id"]
    ).execute()

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt not found"
        )

    receipt = response.data[0]
    student_id = (receipt.get("payments") or {}).get("student_id")
    if student_id:
        PermissionChecker.verify_can_view_student(
            current_user, student_id, db, extra_full_access_roles=("bursar",)
        )
    elif current_user["role"] not in ["admin", "system_admin", "bursar"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this receipt")

    return receipt
