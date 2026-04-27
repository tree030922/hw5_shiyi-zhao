# hw5 — receipt-splitter

## What the skill does

`receipt-splitter` parses a pasted plain-text receipt or restaurant bill, assigns line items to specific people, and computes exactly how much each person owes — including their proportional share of tax, tip, and any fees.

## Why I chose it

Splitting a bill sounds simple, but it is a perfect example of a task where a language model alone is genuinely unreliable. Models make arithmetic mistakes, lose track of proportional tax allocation, and silently round wrong. The script handles all numeric work with Python's `Decimal` type (no floating-point errors), while the model handles the conversational layer: asking for clarifications, formatting the summary, and generating a friendly payment note.

## How to use it

1. Open a project in VS Code with GitHub Copilot Agent enabled.
2. Place the `.agents/` folder at the root of your project.
3. Paste a receipt into chat and tell Copilot who ordered what:

```
Here's our dinner bill. Alice had the pizza and salad, Bob had the pasta and wine. Can you split it?

[paste receipt text]
```

4. Copilot will invoke the skill, run `split_receipt.py`, and return a clean breakdown.

### Manual script usage

```bash
python .agents/skills/receipt-splitter/scripts/split_receipt.py \
  --receipt my_receipt.txt \
  --assignments my_assignments.json \
  --tip 18
```

**`my_assignments.json`** maps item names (exactly as they appear on the receipt) to person names or `"shared"`:

```json
{
  "Margherita Pizza": "Alice",
  "Spaghetti Carbonara": "Bob",
  "Tax (8.5%)": "shared",
  "Tip (18%)": "shared"
}
```

## What the script does

`scripts/split_receipt.py` does four things code must do:

1. **Parses** the receipt line by line with regex, extracting item names and `$XX.XX` prices.
2. **Classifies** lines automatically as shared (tax, tip, service fee, etc.) using keyword matching.
3. **Allocates** shared costs proportionally based on each person's personal subtotal using `Decimal` arithmetic.
4. **Fixes rounding** — any penny discrepancy from proportional allocation is assigned to the highest-spending person, ensuring the sum always matches the grand total.

Output is structured JSON, which the agent formats into a readable summary.

## What worked well

- Using `Decimal` throughout eliminates floating-point surprises entirely.
- Automatic keyword detection for shared items (tax, tip, VAT, delivery fee) means users rarely need to mark them manually.
- The script exits with a clear JSON error if any item is unassigned, prompting the agent to ask the user for clarification rather than silently guessing.
- The `--tip` flag lets users add a tip that wasn't printed on the receipt.

## Limitations

- Input must be **plain text** — images or PDFs are not supported.
- Item names in `assignments.json` must match the receipt text exactly (case-insensitive). Fuzzy matching is not implemented.
- Split items (e.g. "Alice and Bob share the nachos 50/50") require the user to pre-split them into two entries.
- Rounding is deterministic but opinionated — the largest spender absorbs any residual penny.

## Demo video

[[Video link here]](https://youtu.be/wlo-o5kmMxE)
