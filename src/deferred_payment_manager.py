"""
Deferred Payment Manager

Tracks expenses that should have been paid but were deferred to future months.
Handles accrual accounting vs cash accounting.
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from models import ExpenseCategory, ExpenseType


@dataclass
class DeferredPayment:
    """Represents a deferred/pending payment"""

    payment_id: str
    description: str
    amount: Decimal
    category: ExpenseCategory
    expense_type: ExpenseType  # SHARED or INDIVIDUAL

    # Timing
    accrual_month: date  # When expense was incurred (belongs to this month)
    payment_month: Optional[date]  # When it will/was actually paid

    # Responsibility
    responsible_person: str  # Who should pay or who paid
    paid_by: Optional[str]  # Who actually paid (if paid)

    # Status
    status: str  # PENDING, PAID, CANCELLED

    # Notes
    reason: str  # Why deferred
    notes: str

    # Tracking
    created_date: datetime
    paid_date: Optional[datetime]


class DeferredPaymentManager:
    """Manages deferred/pending payments"""

    def __init__(self, storage_path: Path):
        """
        Initialize manager

        Args:
            storage_path: Path to deferred_payments.xlsx
        """
        self.storage_path = Path(storage_path)
        self.payments: List[DeferredPayment] = []

        if self.storage_path.exists():
            self.load()

    def add_deferred_payment(
        self,
        description: str,
        amount: Decimal,
        category: ExpenseCategory,
        expense_type: ExpenseType,
        accrual_month: date,
        responsible_person: str,
        reason: str,
        payment_month: Optional[date] = None,
        notes: str = ""
    ) -> DeferredPayment:
        """
        Add a new deferred payment

        Args:
            description: Expense description
            amount: Amount in Rands
            category: Expense category
            expense_type: SHARED or INDIVIDUAL
            accrual_month: Month when expense was incurred
            responsible_person: Who should pay
            reason: Why deferred
            payment_month: When it will be paid (optional)
            notes: Additional notes

        Returns:
            DeferredPayment object
        """
        payment_id = self._generate_id()

        payment = DeferredPayment(
            payment_id=payment_id,
            description=description,
            amount=amount,
            category=category,
            expense_type=expense_type,
            accrual_month=accrual_month,
            payment_month=payment_month,
            responsible_person=responsible_person,
            paid_by=None,
            status="PENDING",
            reason=reason,
            notes=notes,
            created_date=datetime.now(),
            paid_date=None
        )

        self.payments.append(payment)
        self.save()

        return payment

    def mark_as_paid(
        self,
        payment_id: str,
        paid_by: str,
        payment_month: date,
        paid_date: Optional[datetime] = None
    ) -> None:
        """
        Mark a deferred payment as paid

        Args:
            payment_id: ID of the payment
            paid_by: Who paid it
            payment_month: Month when paid
            paid_date: Date when paid (default: now)
        """
        payment = self._find_payment(payment_id)

        if payment:
            payment.status = "PAID"
            payment.paid_by = paid_by
            payment.payment_month = payment_month
            payment.paid_date = paid_date or datetime.now()
            self.save()

    def cancel_payment(self, payment_id: str, reason: str = "") -> None:
        """
        Cancel a deferred payment

        Args:
            payment_id: ID of the payment
            reason: Reason for cancellation
        """
        payment = self._find_payment(payment_id)

        if payment:
            payment.status = "CANCELLED"
            if reason:
                payment.notes += f"\nCancelled: {reason}"
            self.save()

    def get_pending_payments(self, person: Optional[str] = None) -> List[DeferredPayment]:
        """
        Get all pending payments

        Args:
            person: Filter by responsible person (optional)

        Returns:
            List of pending payments
        """
        pending = [p for p in self.payments if p.status == "PENDING"]

        if person:
            pending = [p for p in pending if p.responsible_person == person]

        return pending

    def get_payments_for_month(
        self,
        month: date,
        by: str = "accrual"
    ) -> List[DeferredPayment]:
        """
        Get payments for a specific month

        Args:
            month: Month to query
            by: "accrual" (when incurred) or "payment" (when paid)

        Returns:
            List of payments
        """
        month_key = month.replace(day=1)

        if by == "accrual":
            return [
                p for p in self.payments
                if p.accrual_month.replace(day=1) == month_key
            ]
        elif by == "payment":
            return [
                p for p in self.payments
                if p.payment_month and p.payment_month.replace(day=1) == month_key
            ]

        return []

    def get_accrual_adjustments(self, month: date) -> Dict[str, Decimal]:
        """
        Get accrual adjustments for a month

        Returns amounts that should be added/subtracted from the month's totals
        to reflect accrual accounting.

        Args:
            month: Month to calculate adjustments for

        Returns:
            Dict with 'add' (expenses incurred this month, paid later)
            and 'subtract' (expenses paid this month, incurred earlier)
        """
        month_key = month.replace(day=1)

        # Expenses incurred this month but paid later (add to this month)
        incurred_here = [
            p for p in self.payments
            if p.accrual_month.replace(day=1) == month_key
            and p.payment_month
            and p.payment_month.replace(day=1) != month_key
        ]

        # Expenses paid this month but incurred earlier (subtract from this month)
        paid_here = [
            p for p in self.payments
            if p.payment_month
            and p.payment_month.replace(day=1) == month_key
            and p.accrual_month.replace(day=1) != month_key
        ]

        add_amount = sum(p.amount for p in incurred_here)
        subtract_amount = sum(p.amount for p in paid_here)

        return {
            "add_incurred_not_paid": add_amount,
            "subtract_paid_not_incurred": subtract_amount,
            "net_adjustment": add_amount - subtract_amount,
            "incurred_count": len(incurred_here),
            "paid_count": len(paid_here)
        }

    def _find_payment(self, payment_id: str) -> Optional[DeferredPayment]:
        """Find payment by ID"""
        for payment in self.payments:
            if payment.payment_id == payment_id:
                return payment
        return None

    def _generate_id(self) -> str:
        """Generate unique payment ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        count = len(self.payments)
        return f"DEF{timestamp}{count:04d}"

    def load(self) -> None:
        """Load deferred payments from Excel"""
        try:
            df = pd.read_excel(self.storage_path)

            self.payments = []
            for _, row in df.iterrows():
                payment = DeferredPayment(
                    payment_id=row["payment_id"],
                    description=row["description"],
                    amount=Decimal(str(row["amount"])),
                    category=ExpenseCategory[row["category"]],
                    expense_type=ExpenseType[row["expense_type"]],
                    accrual_month=pd.to_datetime(row["accrual_month"]).date(),
                    payment_month=pd.to_datetime(row["payment_month"]).date()
                    if pd.notna(row["payment_month"]) else None,
                    responsible_person=row["responsible_person"],
                    paid_by=row["paid_by"] if pd.notna(row["paid_by"]) else None,
                    status=row["status"],
                    reason=row["reason"],
                    notes=row["notes"] if pd.notna(row["notes"]) else "",
                    created_date=pd.to_datetime(row["created_date"]),
                    paid_date=pd.to_datetime(row["paid_date"])
                    if pd.notna(row["paid_date"]) else None
                )
                self.payments.append(payment)

        except Exception as e:
            print(f"Error loading deferred payments: {e}")

    def save(self) -> None:
        """Save deferred payments to Excel"""
        data = []

        for payment in self.payments:
            data.append({
                "payment_id": payment.payment_id,
                "description": payment.description,
                "amount": float(payment.amount),
                "category": payment.category.name,
                "expense_type": payment.expense_type.name,
                "accrual_month": payment.accrual_month.strftime("%Y-%m-%d"),
                "payment_month": payment.payment_month.strftime("%Y-%m-%d")
                if payment.payment_month else "",
                "responsible_person": payment.responsible_person,
                "paid_by": payment.paid_by or "",
                "status": payment.status,
                "reason": payment.reason,
                "notes": payment.notes,
                "created_date": payment.created_date.isoformat(),
                "paid_date": payment.paid_date.isoformat() if payment.paid_date else ""
            })

        df = pd.DataFrame(data)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(self.storage_path, index=False)

    def generate_report(self) -> str:
        """Generate a summary report of deferred payments"""
        report = []
        report.append("=" * 80)
        report.append("DEFERRED PAYMENTS REPORT")
        report.append("=" * 80)

        # Pending payments
        pending = self.get_pending_payments()
        report.append(f"\nPending Payments: {len(pending)}")
        report.append(f"Total Amount: R{sum(p.amount for p in pending):,.2f}")

        if pending:
            report.append("\nDetails:")
            for p in pending:
                report.append(f"  [{p.payment_id}] {p.description}")
                report.append(f"    Amount: R{p.amount:,.2f}")
                report.append(f"    Incurred: {p.accrual_month.strftime('%B %Y')}")
                report.append(f"    Responsible: {p.responsible_person}")
                report.append(f"    Reason: {p.reason}")
                if p.payment_month:
                    report.append(f"    Expected Payment: {p.payment_month.strftime('%B %Y')}")
                report.append("")

        # Paid payments
        paid = [p for p in self.payments if p.status == "PAID"]
        report.append(f"\nPaid (Previously Deferred): {len(paid)}")
        report.append(f"Total Amount: R{sum(p.amount for p in paid):,.2f}")

        # By person
        report.append("\nBy Person:")
        persons = set(p.responsible_person for p in self.payments)
        for person in persons:
            person_pending = [p for p in pending if p.responsible_person == person]
            if person_pending:
                total = sum(p.amount for p in person_pending)
                report.append(f"  {person}: {len(person_pending)} pending (R{total:,.2f})")

        return "\n".join(report)
