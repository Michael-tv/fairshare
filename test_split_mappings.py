#!/usr/bin/env python3
"""
Test script for split mappings functionality.

This demonstrates how to use the split mapping system to split a single
transaction into multiple parts (e.g., HOUSEHOLD and INDIVIDUAL).
"""

from decimal import Decimal
from pathlib import Path
from src.transaction_classifier import TransactionClassifier, SplitPart

def test_split_mappings():
    """Test the split mapping functionality."""
    print("=== Testing Split Mappings ===\n")

    # Create a temporary directory for test data
    test_dir = Path("/tmp/fairshare_test")
    test_dir.mkdir(exist_ok=True)

    # Initialize classifier with split mappings support
    split_mappings_path = test_dir / "split_mappings.json"
    classifier = TransactionClassifier(
        account_id="test_account",
        split_mappings_path=split_mappings_path
    )

    # Test 1: Add a split mapping
    print("Test 1: Adding a split mapping")
    print("-" * 50)

    date = "2024-11-15"
    description = "Woolworths Rondebosch"
    total_amount = Decimal("350.00")

    split_parts = [
        SplitPart(expense_type="HOUSEHOLD", amount=Decimal("280.00"), note="groceries"),
        SplitPart(expense_type="INDIVIDUAL", amount=Decimal("70.00"), note="personal treats"),
    ]

    try:
        classifier.add_split_mapping(date, description, total_amount, split_parts)
        print(f"✓ Successfully added split mapping for {description}")
        print(f"  Total: R{total_amount}")
        print(f"  Parts:")
        for part in split_parts:
            print(f"    - {part.expense_type}: R{part.amount} ({part.note})")
    except Exception as e:
        print(f"✗ Failed to add split mapping: {e}")
        return False

    print()

    # Test 2: Classify the transaction
    print("Test 2: Classifying the split transaction")
    print("-" * 50)

    result = classifier.classify_transaction(
        description=description,
        amount=total_amount,
        date=date
    )

    print(f"Classification result: {result}")
    if result == "SPLIT":
        print("✓ Transaction correctly identified as SPLIT")
    else:
        print(f"✗ Expected 'SPLIT' but got '{result}'")
        return False

    print()

    # Test 3: Retrieve split mapping
    print("Test 3: Retrieving split mapping")
    print("-" * 50)

    retrieved_parts = classifier.get_split_mapping(date, description, total_amount)
    if retrieved_parts:
        print(f"✓ Successfully retrieved {len(retrieved_parts)} split parts:")
        for i, part in enumerate(retrieved_parts, 1):
            print(f"  {i}. {part.expense_type}: R{part.amount} ({part.note})")
    else:
        print("✗ Failed to retrieve split mapping")
        return False

    print()

    # Test 4: Expand transaction
    print("Test 4: Expanding split transaction")
    print("-" * 50)

    expanded = classifier.expand_transaction_if_split(
        date=date,
        description=description,
        amount=total_amount,
        category="Groceries",
        account="Main Account"
    )

    if len(expanded) == 2:
        print(f"✓ Transaction expanded into {len(expanded)} parts:")
        for i, txn in enumerate(expanded, 1):
            print(f"\n  Part {i}:")
            print(f"    Description: {txn['description']}")
            print(f"    Amount: R{txn['amount']}")
            print(f"    Type: {txn['type']}")
            print(f"    Split ID: {txn['split_id']}")
    else:
        print(f"✗ Expected 2 parts but got {len(expanded)}")
        return False

    print()

    # Test 5: Test validation (parts must sum to total)
    print("Test 5: Testing validation (invalid split)")
    print("-" * 50)

    invalid_parts = [
        SplitPart(expense_type="HOUSEHOLD", amount=Decimal("100.00"), note="part1"),
        SplitPart(expense_type="INDIVIDUAL", amount=Decimal("50.00"), note="part2"),
    ]

    try:
        classifier.add_split_mapping(date, "Test Invalid", Decimal("200.00"), invalid_parts)
        print("✗ Should have raised ValueError for invalid split")
        return False
    except ValueError as e:
        print(f"✓ Correctly rejected invalid split: {e}")

    print()

    # Test 6: Remove split mapping
    print("Test 6: Removing split mapping")
    print("-" * 50)

    removed = classifier.remove_split_mapping(date, description, total_amount)
    if removed:
        print("✓ Successfully removed split mapping")

        # Verify it's gone
        result = classifier.classify_transaction(
            description=description,
            amount=total_amount,
            date=date
        )
        if result != "SPLIT":
            print(f"✓ Transaction no longer classified as SPLIT (now: {result})")
        else:
            print("✗ Transaction still classified as SPLIT after removal")
            return False
    else:
        print("✗ Failed to remove split mapping")
        return False

    print()
    print("=" * 50)
    print("All tests passed! ✓")
    print("=" * 50)
    return True

if __name__ == "__main__":
    success = test_split_mappings()
    exit(0 if success else 1)
