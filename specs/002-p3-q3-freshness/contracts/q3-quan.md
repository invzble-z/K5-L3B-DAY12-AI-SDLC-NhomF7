# Q3 ↔ inventory interface

- Input: Quan tuning with `tick_hz`, `freshness.quan_decay_per_s`, `freshness.spoiled_below`, menu recipes, and either legacy count stock or a list of `{id, kind, fresh}`.
- Customer fixture: a waiting customer's `reserved` list contains physical item IDs. IDs must exist, match the complete dish recipe, remain usable, and be unique across customers.
- `spoiled` payload is defined by the shared contract: `{item_id, kind, location: "stock"}`.
- `unfulfillable` payload is not currently in the shared contract. Proposed shape: `{customer_id, table_id, dish_id}`. Do not treat it as approved until PO/Integrator decision #16 is closed.
- No `contract_version` change is made here. The current shared manifest is still 1.1, so v1.2 file-loading acceptance remains external integration work.
