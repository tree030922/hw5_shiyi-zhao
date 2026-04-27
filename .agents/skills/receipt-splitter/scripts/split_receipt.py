#!/usr/bin/env python3
"""
receipt-splitter: split_receipt.py

Parses a receipt (plain text) and a JSON assignment map,
then computes how much each person owes including their
proportional share of tax, tip, and fees.

Usage:
    python split_receipt.py --receipt receipt.txt --assignments assignments.json
    python split_receipt.py --receipt receipt.txt --assignments assignments.json --tip 18

Input:
    receipt.txt       — plain text of the bill (one item per line, price at end)
    assignments.json  — { "Item Name": "PersonName" or "shared" }

Output (stdout): JSON with per-person breakdown and totals
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP




SHARED_KEYWORDS = re.compile(
    r'\b(tax|tip|gratuity|service charge|service fee|delivery fee|surcharge|vat|gst)\b',
    re.IGNORECASE
)

PRICE_RE = re.compile(r'\$?\s*(\d+\.\d{2})\s*$')


def parse_receipt(text: str) -> list[dict]:
    """
    Parse raw receipt text into a list of line items.
    Each item: { "name": str, "price": Decimal, "is_shared": bool }
    """
    items = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        price_match = PRICE_RE.search(line)
        if not price_match:
            continue  # skip lines with no price (headers, etc.)

        price = Decimal(price_match.group(1))
        name = line[:price_match.start()].strip().rstrip('.-: ')

        if not name:
            continue

        is_shared = bool(SHARED_KEYWORDS.search(name))
        items.append({"name": name, "price": price, "is_shared": is_shared})

    return items


# ── Assignment resolution ──────────────────────────────────────────────────────

def resolve_assignments(
    items: list[dict],
    assignments: dict[str, str]
) -> tuple[list[dict], list[dict]]:
    """
    Split items into personal and shared buckets using the assignment map.
    Unrecognised items that are not flagged as shared are left unassigned.

    Returns (personal_items, shared_items)
    personal_items: list of { name, price, person }
    shared_items:   list of { name, price }
    """
    # Normalise keys for fuzzy matching
    norm = {k.lower().strip(): v for k, v in assignments.items()}

    personal, shared = [], []
    unassigned = []

    for item in items:
        key = item["name"].lower().strip()

        if item["is_shared"]:
            shared.append({"name": item["name"], "price": item["price"]})
            continue

        if key in norm:
            person = norm[key]
            if person.lower() == "shared":
                shared.append({"name": item["name"], "price": item["price"]})
            else:
                personal.append({"name": item["name"], "price": item["price"], "person": person})
        else:
            unassigned.append(item["name"])

    if unassigned:
        print(
            json.dumps({"error": "unassigned_items", "items": unassigned}),
            file=sys.stderr
        )
        sys.exit(2)

    return personal, shared


# ── Splitting logic ────────────────────────────────────────────────────────────

def split(
    personal: list[dict],
    shared: list[dict],
    extra_tip_pct: Decimal = Decimal("0")
) -> dict:
    """
    Compute each person's total.

    Shared costs (tax, tip, fees) are allocated proportionally to each
    person's personal subtotal.  A rounding penny is assigned to the
    person with the largest subtotal.
    """
    # Per-person subtotals
    subtotals: dict[str, Decimal] = defaultdict(Decimal)
    personal_lines: dict[str, list] = defaultdict(list)

    for item in personal:
        subtotals[item["person"]] += item["price"]
        personal_lines[item["person"]].append(
            {"name": item["name"], "price": str(item["price"])}
        )

    people = list(subtotals.keys())
    grand_personal = sum(subtotals.values())

    # Add extra tip (if user supplied --tip percentage)
    shared_items = list(shared)
    if extra_tip_pct > 0:
        tip_amount = (grand_personal * extra_tip_pct / 100).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        shared_items.append({"name": f"Tip ({extra_tip_pct}%)", "price": tip_amount})

    total_shared = sum(i["price"] for i in shared_items)
    grand_total = grand_personal + total_shared

    # Proportional allocation of shared costs
    shared_alloc: dict[str, Decimal] = {}
    allocated = Decimal("0")

    if grand_personal == 0:
        # Edge case: everyone only ordered shared items — split evenly
        per_person = (total_shared / len(people)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        for p in people:
            shared_alloc[p] = per_person
        allocated = per_person * len(people)
    else:
        for p in people:
            proportion = subtotals[p] / grand_personal
            alloc = (proportion * total_shared).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            shared_alloc[p] = alloc
            allocated += alloc

    # Fix rounding: assign residual to the person with the highest subtotal
    rounding_residual = total_shared - allocated
    if rounding_residual != 0 and people:
        biggest = max(people, key=lambda p: subtotals[p])
        shared_alloc[biggest] += rounding_residual

    # Build result
    result = {
        "people": {},
        "shared_costs": [
            {"name": i["name"], "price": str(i["price"])} for i in shared_items
        ],
        "grand_total": str(grand_total),
    }

    for p in people:
        total_owed = subtotals[p] + shared_alloc[p]
        result["people"][p] = {
            "items": personal_lines[p],
            "subtotal": str(subtotals[p]),
            "shared_cost_share": str(shared_alloc[p]),
            "total": str(total_owed),
        }

    return result


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Split a receipt among multiple people.")
    parser.add_argument("--receipt", required=True, help="Path to plain-text receipt file")
    parser.add_argument("--assignments", required=True, help="Path to JSON assignment file")
    parser.add_argument(
        "--tip", type=float, default=0,
        help="Extra tip percentage to add (e.g. 18 for 18%%)"
    )
    args = parser.parse_args()

    # Load receipt
    try:
        with open(args.receipt, encoding="utf-8") as f:
            receipt_text = f.read()
    except FileNotFoundError:
        print(json.dumps({"error": f"Receipt file not found: {args.receipt}"}))
        sys.exit(1)

    # Load assignments
    try:
        with open(args.assignments, encoding="utf-8") as f:
            assignments = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(json.dumps({"error": f"Assignments file error: {e}"}))
        sys.exit(1)

    items = parse_receipt(receipt_text)

    if not items:
        print(json.dumps({"error": "no_items_parsed", "hint": "Check receipt format — prices must end each line (e.g. $12.00)"}))
        sys.exit(1)

    personal, shared = resolve_assignments(items, assignments)

    result = split(personal, shared, Decimal(str(args.tip)))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
