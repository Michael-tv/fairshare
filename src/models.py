"""
Data models for the home finance splitting system.
"""
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional, List
from decimal import Decimal


# ExpenseCategory is now managed by CategoryManager in category_manager.py
# This provides default categories that are loaded on first run
DEFAULT_EXPENSE_CATEGORIES = {
    "TAX": "Tax",
    "UIF": "UIF",
    "BANK_CHARGES": "Bank Charges",
    "MEDICAL_AID": "Medical Aid",
    "LOANS": "Loans",
    "INSURANCE": "Insurance",
    "UTILITIES": "Utilities",
    "GROCERIES": "Groceries",
    "FUEL": "Fuel",
    "LEVIES": "Levies",
    "RATES": "Rates",
    "SCHOOL_FEES": "School Fees",
    "DOMESTIC_HELP": "Domestic Help",
    "SUBSCRIPTIONS": "Subscriptions",
    "ENTERTAINMENT": "Entertainment",
    "MAINTENANCE": "Maintenance",
    "CLOTHING": "Clothing",
    "HOUSEHOLD": "Household",
    "TRANSPORT": "Transport",
    "OTHER": "Other"
}

# Keep ExpenseCategory as a simple class for backward compatibility
class ExpenseCategory:
    """Expense categories - now managed dynamically via CategoryManager"""
    pass


class ExpenseType(Enum):
    """Type of expense for splitting logic."""
    HOUSEHOLD = "Household"  # Household expense (split proportionally between partners)
    INDIVIDUAL = "Individual"  # Individual/personal expense (paid by specific person only)
    DEDUCTION = "Deduction"  # Deducted from gross income (like tax)


class IncomeType(Enum):
    """Types of income sources."""
    SALARY = "Salary"
    RENTAL = "Rental Income"
    BUSINESS = "Business Income"
    INVESTMENT = "Investment Income"
    OTHER = "Other Income"


@dataclass
class Person:
    """Represents a person in the household."""
    name: str
    gross_income: Decimal = Decimal("0")

    def __str__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash(self.name)


@dataclass
class Income:
    """Represents an income source."""
    person: Person
    amount: Decimal
    income_type: IncomeType
    description: str
    period: date  # Month or date this income applies to

    def __post_init__(self):
        """Ensure amount is Decimal."""
        if not isinstance(self.amount, Decimal):
            self.amount = Decimal(str(self.amount))


@dataclass
class Expense:
    """Represents an expense item."""
    description: str
    amount: Decimal
    category: ExpenseCategory
    expense_type: ExpenseType
    paid_by: Optional[Person] = None  # Who actually paid
    belongs_to: Optional[Person] = None  # For individual expenses, who should pay
    period: Optional[date] = None
    notes: str = ""

    def __post_init__(self):
        """Ensure amount is Decimal and validate expense type."""
        if not isinstance(self.amount, Decimal):
            self.amount = Decimal(str(self.amount))

        # Validate expense type rules
        if self.expense_type == ExpenseType.INDIVIDUAL and self.belongs_to is None:
            raise ValueError("Individual expenses must specify belongs_to person")


@dataclass
class TaxBracket:
    """Represents a tax bracket for calculations."""
    min_income: Decimal
    max_income: Optional[Decimal]  # None means unlimited
    base_tax: Decimal
    marginal_rate: Decimal  # As percentage (e.g., 26 for 26%)

    def calculate_tax(self, taxable_income: Decimal) -> Decimal:
        """Calculate tax for income in this bracket."""
        if taxable_income <= self.min_income:
            return Decimal("0")

        taxable_in_bracket = taxable_income - self.min_income
        if self.max_income is not None:
            taxable_in_bracket = min(taxable_in_bracket, self.max_income - self.min_income)

        return self.base_tax + (taxable_in_bracket * self.marginal_rate / Decimal("100"))


@dataclass
class FinancialPeriod:
    """Represents a financial period (typically a month)."""
    period: date
    people: List[Person]
    incomes: List[Income] = field(default_factory=list)
    expenses: List[Expense] = field(default_factory=list)

    def add_income(self, income: Income):
        """Add income to this period."""
        self.incomes.append(income)

    def add_expense(self, expense: Expense):
        """Add expense to this period."""
        self.expenses.append(expense)

    def get_total_income(self, person: Optional[Person] = None) -> Decimal:
        """Get total income for a person or all people."""
        if person:
            return sum(
                inc.amount for inc in self.incomes if inc.person == person
            )
        return sum(inc.amount for inc in self.incomes)

    def get_total_expenses(
        self,
        expense_type: Optional[ExpenseType] = None,
        person: Optional[Person] = None
    ) -> Decimal:
        """Get total expenses, optionally filtered by type or person."""
        expenses = self.expenses

        if expense_type:
            expenses = [e for e in expenses if e.expense_type == expense_type]

        if person:
            expenses = [
                e for e in expenses
                if e.belongs_to == person or e.paid_by == person
            ]

        return sum(e.amount for e in expenses)

    def get_expenses_by_category(self, category: ExpenseCategory) -> List[Expense]:
        """Get all expenses in a specific category."""
        return [e for e in self.expenses if e.category == category]


@dataclass
class SplitResult:
    """Result of financial split calculation."""
    period: date
    person1: Person
    person2: Person

    # Income details
    person1_gross_income: Decimal
    person2_gross_income: Decimal
    total_gross_income: Decimal

    # Deductions (tax, UIF, etc.)
    person1_deductions: Decimal
    person2_deductions: Decimal
    total_deductions: Decimal

    # Net income after deductions
    person1_net_income: Decimal
    person2_net_income: Decimal
    total_net_income: Decimal

    # Expense details
    total_shared_expenses: Decimal
    person1_individual_expenses: Decimal
    person2_individual_expenses: Decimal

    # Split calculations
    person1_share_proportion: Decimal  # As decimal (e.g., 0.65 for 65%)
    person2_share_proportion: Decimal

    person1_should_pay: Decimal  # What person1 should pay for shared expenses
    person2_should_pay: Decimal

    # What was actually paid
    person1_actually_paid: Decimal
    person2_actually_paid: Decimal

    # Final settlement
    transfer_amount: Decimal  # Positive means person1 pays person2, negative means person2 pays person1
    transfer_from: Person
    transfer_to: Person

    # Remaining amounts after all expenses
    person1_remaining: Decimal
    person2_remaining: Decimal

    def __str__(self) -> str:
        """Human-readable summary."""
        return f"""
Financial Split Summary for {self.period.strftime('%Y-%m')}
{'=' * 60}

Income:
  {self.person1.name}: R{self.person1_gross_income:,.2f} (gross) → R{self.person1_net_income:,.2f} (net)
  {self.person2.name}: R{self.person2_gross_income:,.2f} (gross) → R{self.person2_net_income:,.2f} (net)
  Total: R{self.total_gross_income:,.2f} (gross) → R{self.total_net_income:,.2f} (net)

Shared Expenses: R{self.total_shared_expenses:,.2f}
  {self.person1.name} should pay: R{self.person1_should_pay:,.2f} ({self.person1_share_proportion*100:.1f}%)
  {self.person2.name} should pay: R{self.person2_should_pay:,.2f} ({self.person2_share_proportion*100:.1f}%)

Individual Expenses:
  {self.person1.name}: R{self.person1_individual_expenses:,.2f}
  {self.person2.name}: R{self.person2_individual_expenses:,.2f}

Settlement:
  {self.transfer_from.name} should transfer R{abs(self.transfer_amount):,.2f} to {self.transfer_to.name}

Remaining after all expenses:
  {self.person1.name}: R{self.person1_remaining:,.2f}
  {self.person2.name}: R{self.person2_remaining:,.2f}
"""
