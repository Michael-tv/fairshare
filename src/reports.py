"""
Reporting module for generating various financial reports.
"""
from decimal import Decimal
from typing import Dict, List
from datetime import date
import csv
from io import StringIO

from models import (
    FinancialPeriod, SplitResult, Person, ExpenseCategory,
    ExpenseType, Expense
)


class ReportGenerator:
    """Generates various financial reports."""

    def generate_summary_report(self, split_result: SplitResult) -> str:
        """
        Generate a comprehensive summary report.

        Args:
            split_result: The split calculation result

        Returns:
            Formatted report as string
        """
        lines = []
        lines.append("=" * 80)
        lines.append(f"FINANCIAL SPLIT REPORT - {split_result.period.strftime('%B %Y')}")
        lines.append("=" * 80)
        lines.append("")

        # Income section
        lines.append("INCOME SUMMARY")
        lines.append("-" * 80)
        lines.append(f"{'': <30} {split_result.person1.name: >15} {split_result.person2.name: >15} {'Total': >15}")
        lines.append(f"{'Gross Income': <30} R{split_result.person1_gross_income: >14,.2f} R{split_result.person2_gross_income: >14,.2f} R{split_result.total_gross_income: >14,.2f}")
        lines.append(f"{'Deductions (Tax + UIF)': <30} R{split_result.person1_deductions: >14,.2f} R{split_result.person2_deductions: >14,.2f} R{split_result.total_deductions: >14,.2f}")
        lines.append(f"{'Net Income': <30} R{split_result.person1_net_income: >14,.2f} R{split_result.person2_net_income: >14,.2f} R{split_result.total_net_income: >14,.2f}")
        lines.append("")

        # Proportions
        lines.append("INCOME PROPORTIONS")
        lines.append("-" * 80)
        lines.append(f"{split_result.person1.name}: {split_result.person1_share_proportion * 100:.1f}%")
        lines.append(f"{split_result.person2.name}: {split_result.person2_share_proportion * 100:.1f}%")
        lines.append("")

        # Expenses section
        lines.append("EXPENSE SUMMARY")
        lines.append("-" * 80)
        lines.append(f"{'Shared Expenses': <40} R{split_result.total_shared_expenses: >14,.2f}")
        lines.append(f"  {split_result.person1.name} should pay ({split_result.person1_share_proportion*100:.1f}%): {'': <15} R{split_result.person1_should_pay: >14,.2f}")
        lines.append(f"  {split_result.person2.name} should pay ({split_result.person2_share_proportion*100:.1f}%): {'': <15} R{split_result.person2_should_pay: >14,.2f}")
        lines.append("")
        lines.append(f"{split_result.person1.name} Individual Expenses: {'': <15} R{split_result.person1_individual_expenses: >14,.2f}")
        lines.append(f"{split_result.person2.name} Individual Expenses: {'': <15} R{split_result.person2_individual_expenses: >14,.2f}")
        lines.append("")

        # Settlement section
        lines.append("SETTLEMENT")
        lines.append("-" * 80)
        lines.append(f"{split_result.person1.name} actually paid for shared: R{split_result.person1_actually_paid:,.2f}")
        lines.append(f"{split_result.person2.name} actually paid for shared: R{split_result.person2_actually_paid:,.2f}")
        lines.append("")
        lines.append(f"** {split_result.transfer_from.name} should transfer R{split_result.transfer_amount:,.2f} to {split_result.transfer_to.name} **")
        lines.append("")

        # Remaining amounts
        lines.append("REMAINING AFTER ALL EXPENSES")
        lines.append("-" * 80)
        lines.append(f"{split_result.person1.name}: R{split_result.person1_remaining:,.2f}")
        lines.append(f"{split_result.person2.name}: R{split_result.person2_remaining:,.2f}")
        lines.append("")

        lines.append("=" * 80)

        return "\n".join(lines)

    def generate_expense_breakdown(
        self,
        period: FinancialPeriod,
        split_result: SplitResult
    ) -> str:
        """
        Generate detailed expense breakdown by category.

        Args:
            period: Financial period
            split_result: Split calculation result

        Returns:
            Formatted report as string
        """
        lines = []
        lines.append("=" * 80)
        lines.append(f"EXPENSE BREAKDOWN - {period.period.strftime('%B %Y')}")
        lines.append("=" * 80)
        lines.append("")

        # Group expenses by category
        category_totals: Dict[ExpenseCategory, Decimal] = {}
        category_details: Dict[ExpenseCategory, List[Expense]] = {}

        for expense in period.expenses:
            if expense.category not in category_totals:
                category_totals[expense.category] = Decimal("0")
                category_details[expense.category] = []

            category_totals[expense.category] += expense.amount
            category_details[expense.category].append(expense)

        # Sort categories by total amount (descending)
        sorted_categories = sorted(
            category_totals.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Display each category
        for category, total in sorted_categories:
            lines.append(f"{category.value.upper()}: R{total:,.2f}")
            lines.append("-" * 80)

            # Show details
            for expense in category_details[category]:
                expense_type_str = expense.expense_type.value
                owner = expense.belongs_to.name if expense.belongs_to else "Shared"
                paid_by = expense.paid_by.name if expense.paid_by else "N/A"

                lines.append(f"  {expense.description: <40} R{expense.amount: >10,.2f}  [{expense_type_str}] Owner: {owner}, Paid by: {paid_by}")

            lines.append("")

        # Total
        total_expenses = sum(e.amount for e in period.expenses)
        lines.append("=" * 80)
        lines.append(f"{'TOTAL EXPENSES': <52} R{total_expenses: >10,.2f}")
        lines.append("=" * 80)

        return "\n".join(lines)

    def generate_category_summary(
        self,
        period: FinancialPeriod
    ) -> str:
        """
        Generate a summary showing percentage of expenses by category.

        Args:
            period: Financial period

        Returns:
            Formatted report as string
        """
        lines = []
        lines.append("=" * 80)
        lines.append(f"EXPENSE CATEGORY SUMMARY - {period.period.strftime('%B %Y')}")
        lines.append("=" * 80)
        lines.append("")

        # Calculate totals by category
        category_totals: Dict[ExpenseCategory, Decimal] = {}
        for expense in period.expenses:
            if expense.category not in category_totals:
                category_totals[expense.category] = Decimal("0")
            category_totals[expense.category] += expense.amount

        total = sum(category_totals.values())

        # Sort by amount
        sorted_categories = sorted(
            category_totals.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Display
        lines.append(f"{'Category': <30} {'Amount': >15} {'Percentage': >15}")
        lines.append("-" * 80)

        for category, amount in sorted_categories:
            percentage = (amount / total * 100) if total > 0 else Decimal("0")
            bar = "#" * int(percentage / 2)  # Simple bar chart (using # for compatibility)
            lines.append(f"{category.value: <30} R{amount: >13,.2f} {percentage: >6.1f}% {bar}")

        lines.append("-" * 80)
        lines.append(f"{'TOTAL': <30} R{total: >13,.2f} {100.0: >6.1f}%")
        lines.append("=" * 80)

        return "\n".join(lines)

    def generate_comparison_report(
        self,
        results: Dict[str, SplitResult]
    ) -> str:
        """
        Generate a comparison report across multiple scenarios or periods.

        Args:
            results: Dictionary mapping scenario names to SplitResults

        Returns:
            Formatted comparison report
        """
        lines = []
        lines.append("=" * 100)
        lines.append("SCENARIO COMPARISON REPORT")
        lines.append("=" * 100)
        lines.append("")

        # Header
        scenarios = list(results.keys())
        header = f"{'Metric': <40}"
        for scenario in scenarios:
            header += f"{scenario: >20}"
        lines.append(header)
        lines.append("-" * 100)

        # Comparison rows
        metrics = [
            ("Total Gross Income", lambda r: r.total_gross_income),
            ("Total Net Income", lambda r: r.total_net_income),
            ("Total Deductions", lambda r: r.total_deductions),
            ("Total Shared Expenses", lambda r: r.total_shared_expenses),
            ("Transfer Amount", lambda r: r.transfer_amount),
            (f"{results[scenarios[0]].person1.name} Remaining", lambda r: r.person1_remaining),
            (f"{results[scenarios[0]].person2.name} Remaining", lambda r: r.person2_remaining),
        ]

        for metric_name, metric_func in metrics:
            row = f"{metric_name: <40}"
            for scenario in scenarios:
                value = metric_func(results[scenario])
                row += f"R{value: >18,.2f}"
            lines.append(row)

        lines.append("=" * 100)

        return "\n".join(lines)

    def export_to_csv(
        self,
        period: FinancialPeriod,
        split_result: SplitResult
    ) -> str:
        """
        Export data to CSV format.

        Args:
            period: Financial period
            split_result: Split calculation result

        Returns:
            CSV string
        """
        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "Description",
            "Amount",
            "Category",
            "Expense Type",
            "Belongs To",
            "Paid By",
            "Date"
        ])

        # Write expenses
        for expense in period.expenses:
            writer.writerow([
                expense.description,
                float(expense.amount),
                expense.category.value,
                expense.expense_type.value,
                expense.belongs_to.name if expense.belongs_to else "",
                expense.paid_by.name if expense.paid_by else "",
                expense.period.strftime("%Y-%m-%d") if expense.period else ""
            ])

        return output.getvalue()

    def generate_yearly_summary(
        self,
        monthly_results: List[SplitResult]
    ) -> str:
        """
        Generate a yearly summary from monthly results.

        Args:
            monthly_results: List of monthly SplitResults

        Returns:
            Formatted yearly summary
        """
        if not monthly_results:
            return "No data available"

        lines = []
        lines.append("=" * 80)
        lines.append("YEARLY SUMMARY")
        lines.append("=" * 80)
        lines.append("")

        # Calculate yearly totals
        total_gross_income = sum(r.total_gross_income for r in monthly_results)
        total_net_income = sum(r.total_net_income for r in monthly_results)
        total_deductions = sum(r.total_deductions for r in monthly_results)
        total_shared_expenses = sum(r.total_shared_expenses for r in monthly_results)
        total_transfers = sum(r.transfer_amount for r in monthly_results)

        person1 = monthly_results[0].person1
        person2 = monthly_results[0].person2

        person1_total_gross = sum(r.person1_gross_income for r in monthly_results)
        person2_total_gross = sum(r.person2_gross_income for r in monthly_results)
        person1_total_net = sum(r.person1_net_income for r in monthly_results)
        person2_total_net = sum(r.person2_net_income for r in monthly_results)

        lines.append(f"Total Gross Income:     R{total_gross_income:,.2f}")
        lines.append(f"  {person1.name: <20} R{person1_total_gross:,.2f}")
        lines.append(f"  {person2.name: <20} R{person2_total_gross:,.2f}")
        lines.append("")
        lines.append(f"Total Net Income:       R{total_net_income:,.2f}")
        lines.append(f"  {person1.name: <20} R{person1_total_net:,.2f}")
        lines.append(f"  {person2.name: <20} R{person2_total_net:,.2f}")
        lines.append("")
        lines.append(f"Total Deductions:       R{total_deductions:,.2f}")
        lines.append(f"Total Shared Expenses:  R{total_shared_expenses:,.2f}")
        lines.append(f"Total Transfers:        R{total_transfers:,.2f}")
        lines.append("")

        # Monthly breakdown
        lines.append("MONTHLY BREAKDOWN")
        lines.append("-" * 80)
        lines.append(f"{'Month': <15} {'Gross Income': >15} {'Net Income': >15} {'Expenses': >15} {'Transfer': >15}")
        lines.append("-" * 80)

        for result in monthly_results:
            month_str = result.period.strftime("%Y-%m")
            lines.append(
                f"{month_str: <15} "
                f"R{result.total_gross_income: >13,.2f} "
                f"R{result.total_net_income: >13,.2f} "
                f"R{result.total_shared_expenses: >13,.2f} "
                f"R{result.transfer_amount: >13,.2f}"
            )

        lines.append("=" * 80)

        return "\n".join(lines)
