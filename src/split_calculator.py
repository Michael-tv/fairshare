"""
Financial split calculator.
Calculates fair splits of expenses based on proportional income.
"""
from decimal import Decimal
from typing import List, Dict, Tuple
from datetime import date

from models import (
    Person, Income, Expense, FinancialPeriod, SplitResult,
    ExpenseType, ExpenseCategory
)


class FinancialSplitter:
    """
    Handles the calculation of fair financial splits between partners.

    The logic:
    1. Calculate net income for each person (after tax/UIF)
    2. Determine shared expenses
    3. Calculate proportional shares based on net income
    4. Determine who owes whom
    """

    def __init__(self, tax_year: int = 2024):
        """
        Initialize the splitter.

        Args:
            tax_year: Tax year (no longer used - kept for compatibility)
        """
        pass

    def calculate_split(
        self,
        period: FinancialPeriod,
        person1: Person,
        person2: Person,
        person1_age: int = 18,
        person2_age: int = 18,
        use_gross_income_for_split: bool = False,
        skip_tax_calculation: bool = False
    ) -> SplitResult:
        """
        Calculate the financial split for a period.

        Args:
            period: FinancialPeriod with all income and expenses
            person1: First person
            person2: Second person
            person1_age: Age of person1 (for tax calculation)
            person2_age: Age of person2 (for tax calculation)
            use_gross_income_for_split: If True, use gross income for proportional split.
                                        If False, use net income (after tax).
            skip_tax_calculation: If True, treat income as NET (take-home) and don't
                                 calculate tax. Use this when entering net salary from payslips.

        Returns:
            SplitResult with all calculations
        """
        # Calculate gross incomes (or NET if skip_tax_calculation)
        person1_gross = period.get_total_income(person1)
        person2_gross = period.get_total_income(person2)
        total_gross = person1_gross + person2_gross

        # Calculate deductions (tax + UIF) - skip if using net income
        if skip_tax_calculation:
            # Treat income as already NET, no tax calculation needed
            person1_deductions = Decimal("0")
            person2_deductions = Decimal("0")
            total_deductions = Decimal("0")
        else:
            # Calculate tax deductions from gross income
            person1_deductions = self._calculate_deductions(period, person1, person1_age)
            person2_deductions = self._calculate_deductions(period, person2, person2_age)
            total_deductions = person1_deductions + person2_deductions

        # Calculate net incomes
        person1_net = person1_gross - person1_deductions
        person2_net = person2_gross - person2_deductions
        total_net = person1_net + person2_net

        # Determine which income to use for split calculation
        if use_gross_income_for_split:
            split_base_p1 = person1_gross
            split_base_p2 = person2_gross
            split_base_total = total_gross
        else:
            split_base_p1 = person1_net
            split_base_p2 = person2_net
            split_base_total = total_net

        # Calculate proportions (avoid division by zero)
        if split_base_total > 0:
            person1_proportion = split_base_p1 / split_base_total
            person2_proportion = split_base_p2 / split_base_total
        else:
            person1_proportion = Decimal("0.5")
            person2_proportion = Decimal("0.5")

        # Get shared expenses
        shared_expenses = self._get_expenses_by_type(period, ExpenseType.HOUSEHOLD)
        total_shared = sum(e.amount for e in shared_expenses)

        # Calculate what each person should pay for shared expenses
        person1_should_pay = total_shared * person1_proportion
        person2_should_pay = total_shared * person2_proportion

        # Get individual expenses
        person1_individual = self._get_individual_expenses(period, person1)
        person2_individual = self._get_individual_expenses(period, person2)

        # Calculate what was actually paid by each person
        person1_paid = self._get_amount_paid_by(period, person1)
        person2_paid = self._get_amount_paid_by(period, person2)

        # Calculate the settlement
        # Person1's balance: what they paid minus what they should have paid
        person1_balance = person1_paid - (person1_should_pay + person1_individual)
        person2_balance = person2_paid - (person2_should_pay + person2_individual)

        # Determine transfer amount and direction
        # If person1_balance is positive, they overpaid and should receive money
        # If person1_balance is negative, they underpaid and should pay money
        if person1_balance >= 0:
            # Person1 overpaid, person2 should pay person1
            transfer_amount = abs(person1_balance)
            transfer_from = person2
            transfer_to = person1
        else:
            # Person1 underpaid, person1 should pay person2
            transfer_amount = abs(person1_balance)
            transfer_from = person1
            transfer_to = person2

        # Calculate remaining amounts after all expenses
        total_expenses = total_shared + person1_individual + person2_individual
        person1_remaining = person1_net - person1_should_pay - person1_individual
        person2_remaining = person2_net - person2_should_pay - person2_individual

        return SplitResult(
            period=period.period,
            person1=person1,
            person2=person2,
            person1_gross_income=person1_gross,
            person2_gross_income=person2_gross,
            total_gross_income=total_gross,
            person1_deductions=person1_deductions,
            person2_deductions=person2_deductions,
            total_deductions=total_deductions,
            person1_net_income=person1_net,
            person2_net_income=person2_net,
            total_net_income=total_net,
            total_shared_expenses=total_shared,
            person1_individual_expenses=person1_individual,
            person2_individual_expenses=person2_individual,
            person1_share_proportion=person1_proportion,
            person2_share_proportion=person2_proportion,
            person1_should_pay=person1_should_pay,
            person2_should_pay=person2_should_pay,
            person1_actually_paid=person1_paid,
            person2_actually_paid=person2_paid,
            transfer_amount=transfer_amount,
            transfer_from=transfer_from,
            transfer_to=transfer_to,
            person1_remaining=person1_remaining,
            person2_remaining=person2_remaining
        )

    def _calculate_deductions(
        self,
        period: FinancialPeriod,
        person: Person,
        age: int
    ) -> Decimal:
        """
        Calculate total deductions (tax + UIF) for a person.

        First checks if deductions are already in expenses (as DEDUCTION type),
        otherwise calculates them from income.
        """
        # Check if deductions are already recorded as expenses
        deduction_expenses = [
            e for e in period.expenses
            if e.expense_type == ExpenseType.DEDUCTION and e.belongs_to == person
        ]

        if deduction_expenses:
            # Use recorded deductions
            return sum(e.amount for e in deduction_expenses)
        else:
            # Tax calculation removed - GROSS mode no longer supported
            # Always use NET income mode (skip_tax_calculation=True)
            return Decimal("0")

    def _get_expenses_by_type(
        self,
        period: FinancialPeriod,
        expense_type: ExpenseType
    ) -> List[Expense]:
        """Get all expenses of a specific type."""
        return [e for e in period.expenses if e.expense_type == expense_type]

    def _get_individual_expenses(
        self,
        period: FinancialPeriod,
        person: Person
    ) -> Decimal:
        """Get total individual expenses for a person."""
        individual_expenses = [
            e for e in period.expenses
            if e.expense_type == ExpenseType.INDIVIDUAL and e.belongs_to == person
        ]
        return sum(e.amount for e in individual_expenses)

    def _get_amount_paid_by(
        self,
        period: FinancialPeriod,
        person: Person
    ) -> Decimal:
        """
        Get the total amount paid by a person.
        Only counts SHARED expenses (individual expenses are separate).
        """
        paid_expenses = [
            e for e in period.expenses
            if e.expense_type == ExpenseType.HOUSEHOLD and e.paid_by == person
        ]
        return sum(e.amount for e in paid_expenses)

    def get_expense_breakdown(
        self,
        period: FinancialPeriod
    ) -> Dict[ExpenseCategory, Decimal]:
        """
        Get a breakdown of expenses by category.

        Args:
            period: FinancialPeriod to analyze

        Returns:
            Dictionary mapping categories to total amounts
        """
        breakdown = {}
        for expense in period.expenses:
            if expense.category not in breakdown:
                breakdown[expense.category] = Decimal("0")
            breakdown[expense.category] += expense.amount

        return breakdown

    def calculate_yearly_projection(
        self,
        monthly_period: FinancialPeriod,
        person1: Person,
        person2: Person,
        person1_age: int = 18,
        person2_age: int = 18
    ) -> Dict[str, Decimal]:
        """
        Project annual figures based on a monthly period.

        Args:
            monthly_period: A typical monthly financial period
            person1: First person
            person2: Second person
            person1_age: Age of person1
            person2_age: Age of person2

        Returns:
            Dictionary with annual projections
        """
        # Calculate monthly split
        monthly_split = self.calculate_split(
            monthly_period,
            person1,
            person2,
            person1_age,
            person2_age
        )

        # Project to annual
        return {
            "annual_gross_income_p1": monthly_split.person1_gross_income * 12,
            "annual_gross_income_p2": monthly_split.person2_gross_income * 12,
            "annual_net_income_p1": monthly_split.person1_net_income * 12,
            "annual_net_income_p2": monthly_split.person2_net_income * 12,
            "annual_shared_expenses": monthly_split.total_shared_expenses * 12,
            "annual_p1_should_pay": monthly_split.person1_should_pay * 12,
            "annual_p2_should_pay": monthly_split.person2_should_pay * 12,
            "annual_transfer_amount": monthly_split.transfer_amount * 12,
        }

    def compare_scenarios(
        self,
        period: FinancialPeriod,
        person1: Person,
        person2: Person,
        scenarios: List[Tuple[str, Decimal, Decimal]]
    ) -> Dict[str, SplitResult]:
        """
        Compare different income scenarios.

        Args:
            period: Base financial period
            person1: First person
            person2: Second person
            scenarios: List of (name, person1_income, person2_income) tuples

        Returns:
            Dictionary mapping scenario names to SplitResults
        """
        results = {}

        for scenario_name, p1_income, p2_income in scenarios:
            # Create a copy of the period with modified incomes
            scenario_period = FinancialPeriod(
                period=period.period,
                people=period.people,
                expenses=period.expenses.copy()
            )

            # Add scenario incomes
            from models import Income, IncomeType
            scenario_period.add_income(Income(
                person=person1,
                amount=p1_income,
                income_type=IncomeType.SALARY,
                description=f"Scenario: {scenario_name}",
                period=period.period
            ))
            scenario_period.add_income(Income(
                person=person2,
                amount=p2_income,
                income_type=IncomeType.SALARY,
                description=f"Scenario: {scenario_name}",
                period=period.period
            ))

            results[scenario_name] = self.calculate_split(
                scenario_period,
                person1,
                person2
            )

        return results
