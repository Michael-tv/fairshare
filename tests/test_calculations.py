"""
Unit tests for financial calculations.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import unittest
from decimal import Decimal
from datetime import date

from models import (
    Person, Income, Expense, FinancialPeriod,
    IncomeType, ExpenseType, ExpenseCategory
)
from split_calculator import FinancialSplitter


class TestFinancialSplitter(unittest.TestCase):
    """Test financial splitting logic."""

    def setUp(self):
        self.splitter = FinancialSplitter(2024)
        self.michael = Person(name="Michael")
        self.jacqui = Person(name="Jacqui")

    def create_test_period(
        self,
        michael_income: Decimal,
        jacqui_income: Decimal,
        shared_expenses: Decimal
    ) -> FinancialPeriod:
        """Helper to create a test financial period."""
        period = FinancialPeriod(
            period=date(2024, 4, 1),
            people=[self.michael, self.jacqui]
        )

        # Add incomes
        period.add_income(Income(
            person=self.michael,
            amount=michael_income,
            income_type=IncomeType.SALARY,
            description="Salary",
            period=date(2024, 4, 1)
        ))

        period.add_income(Income(
            person=self.jacqui,
            amount=jacqui_income,
            income_type=IncomeType.SALARY,
            description="Salary",
            period=date(2024, 4, 1)
        ))

        # Add shared expenses (paid by Michael for testing)
        period.add_expense(Expense(
            description="Shared expense",
            amount=shared_expenses,
            category=ExpenseCategory.OTHER,
            expense_type=ExpenseType.SHARED,
            paid_by=self.michael
        ))

        return period

    def test_equal_income_split(self):
        """Test split with equal incomes."""
        period = self.create_test_period(
            Decimal("50000"),
            Decimal("50000"),
            Decimal("10000")
        )

        result = self.splitter.calculate_split(
            period,
            self.michael,
            self.jacqui
        )

        # With equal incomes, each should pay 50%
        self.assertAlmostEqual(
            float(result.person1_share_proportion),
            0.5,
            places=2
        )
        self.assertAlmostEqual(
            float(result.person2_share_proportion),
            0.5,
            places=2
        )

    def test_unequal_income_split(self):
        """Test split with unequal incomes (70/30 split)."""
        period = self.create_test_period(
            Decimal("70000"),
            Decimal("30000"),
            Decimal("10000")
        )

        result = self.splitter.calculate_split(
            period,
            self.michael,
            self.jacqui,
            use_gross_income_for_split=True  # Use gross for easier calculation
        )

        # Michael earns 70%, Jacqui earns 30%
        self.assertAlmostEqual(
            float(result.person1_share_proportion),
            0.7,
            places=2
        )
        self.assertAlmostEqual(
            float(result.person2_share_proportion),
            0.3,
            places=2
        )

        # Michael should pay 70% of 10,000 = 7,000
        self.assertAlmostEqual(
            float(result.person1_should_pay),
            7000.0,
            places=0
        )

    def test_transfer_calculation(self):
        """Test that transfer amount is calculated correctly."""
        period = self.create_test_period(
            Decimal("60000"),
            Decimal("40000"),
            Decimal("10000")
        )

        result = self.splitter.calculate_split(
            period,
            self.michael,
            self.jacqui,
            use_gross_income_for_split=True
        )

        # Michael earns 60%, should pay 6,000
        # Jacqui earns 40%, should pay 4,000
        # Michael paid all 10,000
        # So Michael overpaid by 4,000
        # Jacqui should transfer 4,000 to Michael

        self.assertEqual(result.transfer_from, self.jacqui)
        self.assertEqual(result.transfer_to, self.michael)
        self.assertAlmostEqual(
            float(result.transfer_amount),
            4000.0,
            places=0
        )

    def test_individual_expenses(self):
        """Test that individual expenses are handled correctly."""
        period = FinancialPeriod(
            period=date(2024, 4, 1),
            people=[self.michael, self.jacqui]
        )

        # Add incomes
        period.add_income(Income(
            person=self.michael,
            amount=Decimal("50000"),
            income_type=IncomeType.SALARY,
            description="Salary",
            period=date(2024, 4, 1)
        ))

        period.add_income(Income(
            person=self.jacqui,
            amount=Decimal("50000"),
            income_type=IncomeType.SALARY,
            description="Salary",
            period=date(2024, 4, 1)
        ))

        # Add individual expense for Michael
        period.add_expense(Expense(
            description="Michael's car payment",
            amount=Decimal("5000"),
            category=ExpenseCategory.LOANS,
            expense_type=ExpenseType.INDIVIDUAL,
            belongs_to=self.michael
        ))

        # Add shared expense
        period.add_expense(Expense(
            description="Groceries",
            amount=Decimal("4000"),
            category=ExpenseCategory.GROCERIES,
            expense_type=ExpenseType.SHARED,
            paid_by=self.michael
        ))

        result = self.splitter.calculate_split(
            period,
            self.michael,
            self.jacqui
        )

        # Check individual expense is recorded
        self.assertEqual(
            float(result.person1_individual_expenses),
            5000.0
        )
        self.assertEqual(
            float(result.person2_individual_expenses),
            0.0
        )

    def test_expense_breakdown(self):
        """Test expense breakdown by category."""
        period = self.create_test_period(
            Decimal("50000"),
            Decimal("50000"),
            Decimal("5000")
        )

        # Add more expenses in different categories
        period.add_expense(Expense(
            description="Medical Aid",
            amount=Decimal("3000"),
            category=ExpenseCategory.MEDICAL_AID,
            expense_type=ExpenseType.SHARED,
            paid_by=self.michael
        ))

        period.add_expense(Expense(
            description="Internet",
            amount=Decimal("500"),
            category=ExpenseCategory.UTILITIES,
            expense_type=ExpenseType.SHARED,
            paid_by=self.jacqui
        ))

        breakdown = self.splitter.get_expense_breakdown(period)

        # Check breakdown has correct categories
        self.assertIn(ExpenseCategory.OTHER, breakdown)
        self.assertIn(ExpenseCategory.MEDICAL_AID, breakdown)
        self.assertIn(ExpenseCategory.UTILITIES, breakdown)

        # Check amounts
        self.assertEqual(float(breakdown[ExpenseCategory.MEDICAL_AID]), 3000.0)
        self.assertEqual(float(breakdown[ExpenseCategory.UTILITIES]), 500.0)


class TestFinancialPeriod(unittest.TestCase):
    """Test FinancialPeriod model."""

    def test_get_total_income(self):
        """Test total income calculation."""
        michael = Person(name="Michael")
        jacqui = Person(name="Jacqui")

        period = FinancialPeriod(
            period=date(2024, 4, 1),
            people=[michael, jacqui]
        )

        period.add_income(Income(
            person=michael,
            amount=Decimal("50000"),
            income_type=IncomeType.SALARY,
            description="Salary",
            period=date(2024, 4, 1)
        ))

        period.add_income(Income(
            person=jacqui,
            amount=Decimal("30000"),
            income_type=IncomeType.SALARY,
            description="Salary",
            period=date(2024, 4, 1)
        ))

        # Test total for specific person
        self.assertEqual(
            float(period.get_total_income(michael)),
            50000.0
        )

        # Test total for all
        self.assertEqual(
            float(period.get_total_income()),
            80000.0
        )


if __name__ == "__main__":
    unittest.main()
