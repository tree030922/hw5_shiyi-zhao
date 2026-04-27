---
name: receipt-splitter
description: Parses pasted receipt or bill plain text, assigns items to people, splits shared costs (tax, tip, fees) proportionally, and outputs a clear breakdown of what each person owes. Use when the user pastes a receipt or bill and wants to split it among multiple people — especially when some items are shared and others are individual.
---

## When to Use This Skill

Use this skill when:
- The user pastes a receipt, bill, or tab (plain text or roughly formatted)
- They want to split costs among 2 or more people
- Some items belong to specific individuals, others are shared
- Tax, tip, or service fees need to be split proportionally

Do **not** use this skill when:
- The user only wants a total (no splitting needed)
- The input is an image or PDF (this skill requires plain text)
- There is only one person paying

---

## Expected Inputs

The user must provide:
1. **Receipt text** — pasted plain text from a receipt, bill, or menu tab
2. **People's names** — who is splitting the bill
3. **Item assignments** — who ordered what (can be stated naturally, e.g. "Alice had the pasta and the beer")

Shared items (tax, tip, delivery fee, service charge) are split proportionally by default unless the user specifies otherwise.

---

## Step-by-Step Instructions

### Step 1 — Parse the receipt
Ask the agent to run `scripts/split_receipt.py` with the receipt text and assignment info.

The script will:
- Extract all line items and prices from the raw text
- Map each item to a person (or mark it as shared)
- Compute each person's subtotal
- Allocate shared costs (tax, tip, fees) proportionally to each person's subtotal
- Return a structured JSON result

### Step 2 — Present the results
Use the JSON output from the script to generate a clean, human-readable summary:
- Show each person's itemized list
- Show their share of tax/tip/fees
- Show their **total amount owed**
- Optionally suggest a Venmo/payment note

### Step 3 — Handle ambiguity
If any item is unassigned, ask the user to clarify before running the script. Do not guess.

---

## Expected Output Format

```
🧾 Receipt Split Summary
========================

Alice
  • Margherita Pizza     $14.00
  • House Salad           $8.00
  • Share of tax/tip      $3.74
  ─────────────────────────────
  Total: $25.74

Bob
  • Spaghetti Carbonara  $16.00
  • Glass of Wine         $9.00
  • Share of tax/tip      $4.26
  ─────────────────────────────
  Total: $29.26

Grand Total: $55.00 ✓
```

---

## Limitations

- Only works with **plain text** input — not images or scanned PDFs
- Cannot automatically determine who ordered what; the user must provide assignments
- If tip/tax is not listed on the receipt, ask the user if they want to add one
- Rounding may cause the sum to differ from the grand total by $0.01; the script handles this by adjusting the last person's share
- Does not handle split items (e.g. "Alice and Bob share the nachos") unless stated explicitly
