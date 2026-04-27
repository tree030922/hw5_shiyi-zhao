# Test Prompts for receipt-splitter

Use these three prompts when demoing the skill in VS Code Copilot Agent.

---

## Prompt 1 — Normal case

```
Here's our dinner receipt. Alice had the Margherita Pizza and House Salad.
Bob had the Spaghetti Carbonara and Glass of Red Wine. We're splitting the
Tiramisu and Sparkling Water equally. Can you split the bill?

Bella Italia Ristorante
Margherita Pizza         $14.00
Spaghetti Carbonara      $16.00
House Salad               $8.00
Glass of Red Wine         $9.00
Tiramisu                  $7.50
Sparkling Water           $3.00
Tax (8.5%)                $4.89
Tip (18%)                $10.35
TOTAL                    $72.74
```

**Expected:** Alice ~$29, Bob ~$43, grand total $72.74 ✓

---

## Prompt 2 — Edge case (empty bill / no items in range)

```
Can you split this receipt? Just the two of us, Alice and Bob.

Quick Café
Coffee x2                 $8.00
Tax                       $0.68
TOTAL                     $8.68
```

**Expected:** Script handles a bill where all items are shared evenly
(no personal items assigned). Should split $8.68 ÷ 2 = $4.34 each.

---

## Prompt 3 — Caution / partial decline case

```
Here's a receipt. Can you split it?

Joe's Diner
Burger                   $12.00
Fries                     $4.00
Milkshake                 $6.00
Tax                       $1.87
TOTAL                    $23.87
```

(No assignments provided.)

**Expected:** The skill should NOT guess who ordered what. It should ask
the user: "I can see 3 items — Burger, Fries, and Milkshake. Who ordered each?"
The script will exit with an `unassigned_items` error and the agent surfaces
this as a clarifying question.
