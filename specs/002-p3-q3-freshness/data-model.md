# Data model — Q3 stock

## Physical item

Use `chonoi.inventory.Item(id, kind, fresh)`. `fresh` is a `Fraction` in `[0, 100]`. Restaurant `items` remains a list of physical items while `stock` is a derived per-kind count for legacy-compatible recipes and snapshots.

## Customer reservation

- Before cooking: `reserved` is an ordered list of physical item IDs.
- Once cooking consumes the recipe: `reserved` is empty and `consumed_items` holds copied item snapshots for the cook/price interface.
- On customer departure: release changes reservation state once and does not alter physical stock.
- When reserved stock spoils: release the entire ID list and make one replacement attempt. A failed attempt clears IDs and sets `order_status: "unfulfillable"`; the customer remains waiting and patience continues.

## Events

- `spoiled`: `{item_id, kind, location: "stock"}` (shared contract).
- `unfulfillable`: proposed `{customer_id, table_id, dish_id}`; requires contract approval.
