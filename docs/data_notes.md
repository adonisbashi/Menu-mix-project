| Canonical Name | Raw Source  | Type         | Unit / Domain               | Transform Rules                                                  | Examples           |
|----------------|-------------|--------------|-----------------------------|------------------------------------------------------------------|--------------------|
| plu            | PLU         | string       | Non-empty; may start with 0 | Trim whitespace; do **not** cast to int; preserve leading zeros | "000123", "4512"   |
| item_name      | Item Name   | string       | 1–120 characters            | Trim whitespace; collapse multiple spaces; remove non-printing  | "Large Fries"      |
| qty            | Qty         | int          | ≥ 0                         | Coerce to int; if non-numeric or NaN → mark row as non-item      | 64                 |
| gross_cents    | Total $     | int (cents)  | ≥ 0                         | Remove `$` and `,`; convert dollars→cents; round; store as int   | $404.16 → 40416    |
| net_cents      | Net $       | int (cents)  | ≥ 0                         | Same as gross_cents                                              | $385.99 → 38599    |
| sales_pct      | Sales %     | float        | **Choose:** 0–1 or 0–100    | Remove `%`; convert to fraction or percent based on chosen scale | "1.24%" → 0.0124   |

## Normalization Rules

- **Text cleanup:**
  - Trim leading/trailing whitespace on all text columns.
  - Collapse multiple internal spaces into one.
  - Remove non-printing characters (e.g., `\xa0` non-breaking spaces).
  - Keep `plu` as a string to preserve leading zeros.

- **Money parsing:**
  - Remove `$` signs and commas from currency fields.
  - Convert from Decimal dollars to integer cents (`dollars * 100`).
  - Round half up to nearest cent.
  - Store in integer format (no floats).

- **Quantity handling:**
  - Coerce `qty` to integer.
  - If `qty` is NaN or non-numeric, mark the row as a non-item (likely header or subtotal).

- **Percent handling:**
  - Remove `%` symbol from `sales_pct`.
  - Convert to either:
    - Fraction (0–1 range) if `percent_scale = fraction`
    - Percent value (0–100 range) if `percent_scale = percent`
  - Decide once and apply consistently.

- **Header/subtotal detection:**
  - Treat as non-item if:
    - `qty` is NaN or empty **and** both money columns are empty.
    - `plu` is empty **and** `item_name` matches known category headers (e.g., "Appetizers", "AppetizerMods").
  - Maintain a list of known headers in `docs/assumptions.md`.

- **Column ordering after normalization:**
  - `[plu, item_name, qty, gross_cents, net_cents, sales_pct]`


## Validation Checks

Use these to verify the normalized dataset before moving to Day 4.

- **PLU**
  - Must be a string.
  - Leading zeros are preserved (e.g., `"000123"` remains `"000123"`).
  - No empty PLU for sellable items.

- **Item Name**
  - No leading/trailing spaces.
  - No multiple consecutive spaces.
  - No non-printing characters.

- **Quantity**
  - `qty` is an integer ≥ 0.
  - Any non-numeric or missing quantity is correctly marked as a non-item row.

- **Currency Fields**
  - `gross_cents` and `net_cents` are integers in cents (no floats).
  - `gross_cents >= net_cents` for all rows.
  - For rows with `qty > 0`, `net_cents / qty` falls within a reasonable price range (e.g., 50¢ to $200.00).

- **Sales Percentage**
  - `sales_pct` is numeric and matches the chosen scale (0–1 or 0–100).
  - No `%` symbol remains in the normalized value.

- **Non-Item Row Removal**
  - All known category headers (e.g., "Appetizers", "AppetizerMods") are excluded from the normalized preview.
  - No subtotal or group rows are present.

- **Column Order**
  - `[plu, item_name, qty, gross_cents, net_cents, sales_pct]` is consistent across outputs.

- **Sample Export**
  - `data/processed/normalized_sample.csv` contains ~200 clean, representative rows.
  - Spot-check 5–10 random rows against the original export to confirm accuracy.
