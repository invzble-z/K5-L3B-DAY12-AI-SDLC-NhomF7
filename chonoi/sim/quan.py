import math
from fractions import Fraction
"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Phase 1 (PRD-0 mục F, Quán):
  Lát 3: khách đến theo lịch, chọn món nấu được, giữ chỗ nguyên liệu, kiên nhẫn,
                     bỏ đi (customer_left), truy vấn điều kiện no_dish.
  Lát 4: interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
                     ăn xong trả tiền (paid), boa, uy tín, hết ca (quan_end).
"""

from copy import deepcopy

from ..errors import BadInput
from ..ids import sort_by_id
from ..inventory import Item
from .ramp import ramp_velocity


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None, menu_filter=None):
        t = tuning["quan"]
        self.t = t
        self.tick_hz = tuning["tick_hz"]
        self.menu = tuning["menu"]
        # None allows the full menu; an empty filter allows no dishes.
        if menu_filter is None:
            self.planned_dishes = None
        else:
            if not isinstance(menu_filter, (set, frozenset, list, tuple, dict)) or any(
                not isinstance(key, str) or key not in self.menu for key in menu_filter
            ):
                raise BadInput("menu_filter phải chứa các món trong menu")
            self.planned_dishes = frozenset(menu_filter)
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (hỗ trợ cả dict đếm v1.0/1.1 và mảng cá thể v1.2)
        raw_stock = inventory if inventory is not None else scenario.get("stock", {})
        if isinstance(raw_stock, list):
            self.items = [it if isinstance(it, Item) else Item(it["id"], it["kind"], it["fresh"])
                          for it in raw_stock]
            if len({it.id for it in self.items}) != len(self.items):
                raise BadInput("id nguyên liệu bị trùng trong kho quán")
            self.items = sort_by_id(self.items, key=lambda it: it.id)
            counts = {}
            for it in self.items:
                counts[it["kind"]] = counts.get(it["kind"], 0) + 1
            self.stock = counts
        else:
            self.items = []
            self.stock = dict(raw_stock)
        self.freshness_decay = None
        self.spoiled_below = None
        freshness = tuning.get("freshness")
        self.freshness = dict(freshness) if freshness else None
        if self.items and not freshness:
            raise BadInput("kho cá thể cần cấu hình freshness")
        if self.items:
            self.freshness_decay = Fraction(str(freshness["quan_decay_per_s"])) / self.tick_hz
            self.spoiled_below = Fraction(str(freshness["spoiled_below"]))
        random_customers = scenario.get("random_customers", True)
        if not isinstance(random_customers, bool):
            raise BadInput("quan.random_customers phải là boolean")
        self.random_customers = random_customers
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * self.tick_hz)))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            base_price=s.get("base_price"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.customers = []
        self._reservation_state = {}
        for source in sort_by_id(scenario.get("customers", [])):
            c = deepcopy(source)
            dish_id = c.get("dish_id") or c.get("dish") or c.get("order")
            state = c.get("state", "waiting")
            c["dish_id"] = dish_id
            c["order"] = dish_id
            c["order_tick"] = c.get("order_tick", 0)
            c["state"] = state
            order_tick = c.get("order_tick", 0)
            if isinstance(order_tick, bool) or not isinstance(order_tick, int) or order_tick < 0:
                raise BadInput(f"customers.{c['id']}.order_tick phải là số nguyên không âm")
            c["order_tick"] = order_tick
            if "patience_ticks_left" in c:
                patience = int(c["patience_ticks_left"])
            elif "patience_ticks" in c:
                patience = int(c["patience_ticks"])
            elif "patience_s" in c:
                patience = int(round(float(c["patience_s"]) * self.tick_hz))
            else:
                patience = int(round(t["patience_s"] * self.tick_hz))
            c["patience_ticks_left"] = patience
            c["patience_ticks"] = patience
            c["patience_max_ticks"] = c.get(
                "patience_max_ticks", int(round(t["patience_s"] * self.tick_hz)))
            eat_ticks = c.get("eat_ticks_left")
            if eat_ticks is None:
                eat_ticks = int(round(t["eat_s"] * self.tick_hz))
            c["eat_ticks_left"] = int(eat_ticks)
            if state in ("ordered", "eating"):
                reserved = deepcopy(c.get("reserved", {}))
                if isinstance(reserved, dict) and any(reserved.values()):
                    raise BadInput(f"customers.{c['id']}: khách đã nấu không giữ nguyên liệu thô")
                elif isinstance(reserved, list) and reserved:
                    raise BadInput(f"customers.{c['id']}: khách đã nấu không giữ nguyên liệu thô")
                reservation_state = "consumed"
            elif "reserved" in c:
                reserved = deepcopy(c["reserved"])
                if isinstance(reserved, list):
                    reservation_state = "reserved" if reserved else "released"
                else:
                    reservation_state = "reserved" if any(reserved.values()) else "released"
            elif self.hand == dish_id or any(s.get("dish") == dish_id for s in self.stoves):
                reserved = [] if self.items else {}
                reservation_state = "released"
            else:
                if self.items:
                    reserved = []
                    reservation_state = "pending"
                else:
                    reserved = deepcopy(self.menu[dish_id]["recipe"])
                    reservation_state = "reserved"
            if reservation_state == "reserved" and isinstance(reserved, dict) and reserved != self.menu[dish_id]["recipe"]:
                raise BadInput(f"customers.{c['id']}.reserved phải bằng đúng recipe của dish_id")
            c["reserved"] = reserved
            self._reservation_state[c["id"]] = reservation_state
            self.customers.append(c)
        reserved_totals = {}
        for customer in self.customers:
            if self._reservation_state[customer["id"]] != "reserved":
                continue
            res = customer.get("reserved", {})
            if isinstance(res, list):
                if not self._ids_match_recipe(res, self.menu[customer["dish_id"]]["recipe"]):
                    raise BadInput(f"customers.{customer['id']}.reserved không khớp recipe hoặc kho")
                for item_id in res:
                    it = next((x for x in self.items if x["id"] == item_id), None)
                    if it:
                        reserved_totals[it["kind"]] = reserved_totals.get(it["kind"], 0) + 1
            elif isinstance(res, dict):
                for kind, amount in res.items():
                    reserved_totals[kind] = reserved_totals.get(kind, 0) + amount
        if any(self.stock.get(kind, 0) < amount for kind, amount in reserved_totals.items()):
            raise BadInput("nguyên liệu giữ chỗ vượt kho")
        if self.items:
            all_reserved = [item_id for c in self.customers
                            if self._reservation_state.get(c["id"]) == "reserved"
                            for item_id in c.get("reserved", [])]
            if len(all_reserved) != len(set(all_reserved)):
                raise BadInput("một id nguyên liệu không thể được giữ bởi nhiều khách")
            for customer in self.customers:
                if self._reservation_state[customer["id"]] == "pending":
                    self._reservation_state[customer["id"]] = None
                    if not self._reserve_for_customer(customer):
                        raise BadInput(f"customers.{customer['id']}: không thể giữ recipe từ kho cá thể")
        for e in self.customers:
            ids.reserve(e["id"])
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None
        self.elapsed_ticks = 0
        self._freshness_retry_attempted = set()

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                if "pos" in u:
                    by_id[u["id"]] = dict(u)
                else:
                    from ..errors import BadInput
                    raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            else:
                by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        available = self._available_stock()
        if self.items:
            held_ids = self._reserved_item_ids()
            stock_snapshot = [item.snapshot() for item in self.items if item.id not in held_ids]
        else:
            stock_snapshot = {kind: available[kind] for kind in sorted(available)}
        return {
            "player": {"pos": self.pos},
            "stock": stock_snapshot,
            **({"freshness": self.freshness} if self.freshness else {}),
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": sort_by_id(self.customers),
        }

    def step(self, inp):
        events = []
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.elapsed_ticks += 1
        events.extend(self._decay_stock())
        events.extend(self._tick_customers())
        events.extend(self._tick_stoves())
        self._move(inp)
        if inp.pressed("interact"):
            events.extend(self._interact())
        events.extend(self._spawn_customers())
        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            self.hand = None
            for s in self.stoves:
                s["state"] = "idle"
                s["dish"] = None
                s["cook_ticks_left"] = 0
                s["ready_ticks"] = 0
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        return events

    def _available_stock(self):
        if self.items:
            held_ids = self._reserved_item_ids()
            available = {}
            for item in self.items:
                if item.id not in held_ids and item.fresh >= self.spoiled_below:
                    available[item.kind] = available.get(item.kind, 0) + 1
            return available
        reserved = {}
        for c in self.customers:
            reservation = c.get("reserved", {})
            if not isinstance(reservation, dict):
                continue
            if self._reservation_state.get(c["id"]) != "reserved":
                continue
            for kind, amount in reservation.items():
                reserved[kind] = reserved.get(kind, 0) + amount
        return {kind: amount - reserved.get(kind, 0) for kind, amount in self.stock.items()
                if amount - reserved.get(kind, 0) > 0}

    def _has_recipe(self, recipe, available=None):
        available = self._available_stock() if available is None else available
        return all(available.get(kind, 0) >= amount for kind, amount in recipe.items())

    def _reserve_for_customer(self, customer):
        """Atomically reserve a complete recipe without changing physical stock."""
        customer_id = customer["id"]
        dish_id = customer.get("dish_id", customer.get("dish"))
        if dish_id not in self.menu:
            return False
        state = self._reservation_state.get(customer_id)
        recipe = dict(self.menu[dish_id]["recipe"])
        if state == "reserved":
            reservation = customer.get("reserved", {})
            if self.items:
                return isinstance(reservation, list) and self._ids_match_recipe(reservation, recipe)
            return reservation == recipe
        if state in ("consumed", "released"):
            return False
        existing_reserved = customer.get("reserved", {})
        if existing_reserved and not (self.items and isinstance(existing_reserved, list)) and existing_reserved != recipe:
            return False
        if self.items:
            held_ids = self._reserved_item_ids()
            selected = []
            for kind, amount in sorted(recipe.items()):
                candidates = [it for it in self.items if it.kind == kind and it.id not in held_ids
                              and it.fresh >= self.spoiled_below]
                candidates = sorted(candidates, key=lambda it: (-it.fresh, self._id_order(it.id)))
                if len(candidates) < amount:
                    return False
                selected.extend(candidates[:amount])
            customer["dish_id"] = dish_id
            customer["reserved"] = [it.id for it in sort_by_id(selected, key=lambda it: it.id)]
            self._reservation_state[customer_id] = "reserved"
            return True
        if not self._has_recipe(recipe):
            return False
        customer["dish_id"] = dish_id
        customer["reserved"] = recipe
        self._reservation_state[customer_id] = "reserved"
        return True

    def _consume_reservation(self, customer_id):
        """Debit physical stock once and transfer a reserved recipe to cooking."""
        if self._reservation_state.get(customer_id) != "reserved":
            return False
        customer = next((c for c in self.customers if c["id"] == customer_id), None)
        if customer is None:
            return False
        reserved = customer.get("reserved", {})
        recipe = self.menu[customer["dish_id"]]["recipe"]
        consumed_items = []
        if isinstance(reserved, list):
            reserved_ids = set(reserved)
            items_to_consume = [it for it in self.items if it["id"] in reserved_ids]
            kinds_count = {}
            for it in items_to_consume:
                kinds_count[it["kind"]] = kinds_count.get(it["kind"], 0) + 1
            if kinds_count != recipe:
                return False
            self.items = [it for it in self.items if it["id"] not in reserved_ids]
            for it in items_to_consume:
                self.stock[it["kind"]] = max(0, self.stock.get(it["kind"], 0) - 1)
                if self.stock[it["kind"]] == 0:
                    del self.stock[it["kind"]]
            consumed_items = [it.snapshot() if isinstance(it, Item) else dict(it)
                              for it in items_to_consume]
        elif isinstance(reserved, dict):
            if reserved != recipe or any(self.stock.get(kind, 0) < amount for kind, amount in reserved.items()):
                return False
            for kind, amount in reserved.items():
                self.stock[kind] -= amount
                if self.stock[kind] == 0:
                    del self.stock[kind]
            if getattr(self, "items", None):
                for kind, amount in reserved.items():
                    matching = [it for it in self.items if it["kind"] == kind][:amount]
                    consumed_items.extend(matching)
                matching_ids = {it["id"] for it in consumed_items}
                self.items = [it for it in self.items if it["id"] not in matching_ids]
        customer["reserved"] = [] if isinstance(reserved, list) else {}
        customer["consumed_items"] = consumed_items
        self._reservation_state[customer_id] = "consumed"
        return True

    def _release_reservation(self, customer_id):
        """Release an unconsumed reservation once; never add stock back."""
        if self._reservation_state.get(customer_id) != "reserved":
            return {}
        customer = next((c for c in self.customers if c["id"] == customer_id), None)
        if customer is None:
            return {}
        reservation = customer.get("reserved", {})
        released = list(reservation) if isinstance(reservation, list) else dict(reservation)
        customer["reserved"] = [] if isinstance(reservation, list) else {}
        self._reservation_state[customer_id] = "released"
        return released

    def _can_accept_order(self):
        occupied = {c["table_id"] for c in self.customers}
        if not any(tb["id"] not in occupied for tb in self.tables):
            return False
        available = self._available_stock()
        return any(self._has_recipe(self.menu[dish_id]["recipe"], available)
                   for dish_id in self._eligible_dishes())

    def _eligible_dishes(self):
        return sorted(self.menu if self.planned_dishes is None else self.planned_dishes)

    @staticmethod
    def _id_order(ident):
        from ..ids import id_key
        return id_key(ident)

    def _reserved_item_ids(self):
        return {item_id for c in self.customers
                if self._reservation_state.get(c["id"]) == "reserved"
                for item_id in c.get("reserved", []) if isinstance(c.get("reserved"), list)}

    def _ids_match_recipe(self, item_ids, recipe):
        by_id = {it.id: it for it in self.items}
        if len(item_ids) != len(set(item_ids)) or any(item_id not in by_id for item_id in item_ids):
            return False
        counts = {}
        for item_id in item_ids:
            item = by_id[item_id]
            if item.fresh < self.spoiled_below:
                return False
            counts[item.kind] = counts.get(item.kind, 0) + 1
        return counts == recipe

    def _decay_stock(self):
        if not self.items or self.freshness_decay is None:
            return []
        spoiled = []
        for item in sort_by_id(self.items, key=lambda it: it.id):
            before = item.fresh
            item.fresh = max(Fraction(0), before - self.freshness_decay)
            if before >= self.spoiled_below > item.fresh:
                spoiled.append(item)
        events = [("spoiled", {"item_id": item.id, "kind": item.kind, "location": "stock"})
                  for item in spoiled]
        spoiled_ids = {item.id for item in spoiled}
        affected = [c for c in self.customers
                    if self._reservation_state.get(c["id"]) == "reserved"
                    and isinstance(c.get("reserved"), list)
                    and spoiled_ids.intersection(c["reserved"])]
        affected.sort(key=lambda c: (c.get("order_tick", 0), self._id_order(c.get("table_id", ""))))
        for customer in affected:
            cid = customer["id"]
            self._release_reservation(cid)
            customer["reserved"] = []
            self._reservation_state.pop(cid, None)
            customer["order_status"] = "unfulfillable"
            if cid in self._freshness_retry_attempted or not self._reserve_for_customer(customer):
                customer["order_status"] = "unfulfillable"
                events.append(("unfulfillable", {"customer_id": cid,
                                                  "table_id": customer["table_id"],
                                                  "dish_id": customer["dish_id"]}))
            else:
                customer.pop("order_status", None)
            self._freshness_retry_attempted.add(cid)
        return events

    def _has_active_work(self):
        return bool(self.customers or self.hand is not None or
                    any(stove["state"] != "idle" for stove in self.stoves))

    def _spawn_customers(self):
        events = []
        if not self.random_customers:
            return events
        first = int(self.t["first_customer_tick"])
        interval = int(round(self.t["customer_interval_s"] * self.tick_hz))
        if self.elapsed_ticks < first:
            return events
        if (self.elapsed_ticks - first) % interval != 0:
            return events
        occupied = {c["table_id"] for c in self.customers}
        free_tables = [tb for tb in sort_by_id(self.tables) if tb["id"] not in occupied]
        if not free_tables:
            return events
        available = self._available_stock()
        dishes = [dish_id for dish_id in self._eligible_dishes()
                  if self._has_recipe(self.menu[dish_id]["recipe"], available)]
        if not dishes:
            events.append(("no_dish", {}))
            return events
        dish_id = self.rng.get("customer_dish").choice(dishes)
        tb = free_tables[0]
        c = {"id": self.ids.new("C"), "table_id": tb["id"], "dish_id": dish_id,
             "state": "waiting",
             "order": dish_id,
             "order_tick": self.elapsed_ticks,
             "patience_ticks_left": int(round(self.t["patience_s"] * self.tick_hz)),
             "patience_ticks": int(round(self.t["patience_s"] * self.tick_hz)),
             "patience_max_ticks": int(round(self.t["patience_s"] * self.tick_hz)),
             "eat_ticks_left": int(round(self.t["eat_s"] * self.tick_hz)),
             "reserved": {}}
        if not self._reserve_for_customer(c):
            return events
        self.customers.append(c)
        events.append(("customer_arrived", {"customer_id": c["id"], "table_id": tb["id"],
                                             "dish_id": dish_id}))
        return events

    def _tick_customers(self):
        events = []
        remaining = []
        for c in sort_by_id(self.customers):
            if c["state"] == "eating":
                c["eat_ticks_left"] = max(0, int(c.get("eat_ticks_left", 0)) - 1)
                if c["eat_ticks_left"] <= 0:
                    dish_id = c["dish_id"]
                    menu = self.menu[dish_id]
                    price = int(c.get("base_price", menu["price"]))
                    p_max = c.get("patience_max_ticks", self.t["patience_s"] * self.tick_hz)
                    patience_ratio = c.get(
                        "patience_ratio_served",
                        c["patience_ticks_left"] / p_max if p_max > 0 else 1.0,
                    )
                    tip = 0
                    if patience_ratio >= self.t["tip_min_patience_ratio"]:
                        tip = int(math.floor(price * self.t["tip_rate"]))
                        if tip > 0 or self.t.get("tip_reputation", 0) > 0:
                            self.reputation = min(float(self.t["reputation_max"]),
                                                  round(self.reputation + float(self.t["tip_reputation"]), 3))
                    total = price + tip
                    self.money += total
                    self.earned += total
                    self.shift_earned += total
                    events.append(("paid", {"customer_id": c["id"], "table_id": c["table_id"],
                                            "dish_id": dish_id, "dish": dish_id, "price": price,
                                            "money": price, "tip": tip, "reputation": self.reputation,
                                            "patience_ratio": patience_ratio}))
                    continue
            elif c["state"] in ("waiting", "ordered"):
                c["patience_ticks_left"] = max(0, int(c.get("patience_ticks_left", 0)) - 1)
                c["patience_ticks"] = c["patience_ticks_left"]
                if c["patience_ticks_left"] <= 0:
                    self._release_reservation(c["id"])
                    self.reputation = max(float(self.t["reputation_min"]),
                                          self.reputation + float(self.t["left_reputation_delta"]))
                    events.append(("customer_left", {"customer_id": c["id"], "table_id": c["table_id"],
                                                     "dish_id": c["dish_id"]}))
                    continue
            remaining.append(c)
        self.customers = remaining
        return events

    def _tick_stoves(self):
        events = []
        burn_s = self.t.get("burn_s")
        burn_ticks = int(round(burn_s * self.tick_hz)) if (burn_s is not None and burn_s > 0) else None
        for s in sort_by_id(self.stoves):
            if s["state"] == "cooking":
                s["cook_ticks_left"] = max(0, int(s.get("cook_ticks_left", 0)) - 1)
                if s["cook_ticks_left"] <= 0:
                    s["state"] = "ready"
                    s["cook_ticks_left"] = 0
                    s["ready_ticks"] = 0
                    events.append(("dish_ready", {"stove_id": s["id"], "dish_id": s["dish"], "dish": s["dish"]}))
            elif s["state"] == "ready":
                s["ready_ticks"] = int(s.get("ready_ticks", 0)) + 1
                if burn_ticks is not None and s["ready_ticks"] > burn_ticks:
                    s["state"] = "burned"
                    events.append(("dish_burned", {"stove_id": s["id"], "dish_id": s["dish"], "dish": s["dish"]}))
        return events

    def _candidate_interactions(self):
        candidates = []
        for s in sort_by_id(self.stoves):
            dist = ((self.pos[0] - s["pos"][0]) ** 2 + (self.pos[1] - s["pos"][1]) ** 2) ** 0.5
            if dist <= self.t["interact_radius"]:
                candidates.append((round(dist, 5), 0, s["id"], "stove", s))
        for tb in sort_by_id(self.tables):
            dist = ((self.pos[0] - tb["pos"][0]) ** 2 + (self.pos[1] - tb["pos"][1]) ** 2) ** 0.5
            if dist <= self.t["interact_radius"]:
                candidates.append((round(dist, 5), 1, tb["id"], "table", tb))
        candidates.sort(key=lambda item: (item[0], item[1], item[2]))
        return [item[3:] for item in candidates]

    def _nearest_interaction(self):
        cands = self._candidate_interactions()
        return cands[0] if cands else None

    def _has_reserved_recipe(self, customer):
        dish_id = customer.get("dish_id") or customer.get("order")
        if dish_id not in self.menu:
            return False
        recipe = self.menu[dish_id]["recipe"]
        reserved = customer.get("reserved", {})
        if isinstance(reserved, list):
            return self._ids_match_recipe(reserved, recipe)
        return all(reserved.get(kind, 0) >= amount for kind, amount in recipe.items())

    def _try_interact(self, kind, obj):
        events = []
        if kind == "stove":
            if obj["state"] == "idle" and self.hand is None:
                waiting = [c for c in self.customers
                           if c["state"] == "waiting"
                           and self._has_reserved_recipe(c)]
                if waiting:
                    waiting.sort(key=lambda c: (c.get("order_tick", 0), c.get("table_id", ""), c.get("id", "")))
                    c = waiting[0]
                    dish_id = c["dish_id"]
                    if not self._consume_reservation(c["id"]):
                        return events
                    c["state"] = "ordered"
                    obj["state"] = "cooking"
                    obj["dish"] = dish_id
                    obj["cook_ticks_left"] = int(round(self.menu[dish_id]["cook_s"] * self.tick_hz))
                    obj["ready_ticks"] = 0
                    consumed_items = c.get("consumed_items", [])
                    menu_price = self.menu[dish_id]["price"]
                    if consumed_items:
                        sorted_items = sorted(consumed_items, key=lambda it: (it["kind"], it["id"]))
                        sum_fresh = sum(Fraction(str(it.get("fresh", 100))) for it in sorted_items)
                        base_price = int(math.floor(Fraction(menu_price * sum_fresh, 100 * len(sorted_items))))
                        obj["base_price"] = base_price
                        obj["items"] = sorted_items
                        c["base_price"] = base_price
                        events.append(("cook_started", {
                            "stove_id": obj["id"],
                            "customer_id": c["id"],
                            "dish_id": dish_id,
                            "dish": dish_id,
                            "items": [{"id": it["id"], "kind": it["kind"], "fresh": float(it.get("fresh", 100))} for it in sorted_items]
                        }))
                    else:
                        base_price = menu_price
                        obj["base_price"] = base_price
                        c["base_price"] = base_price
                        events.append(("cook_started", {"stove_id": obj["id"], "customer_id": c["id"],
                                                        "dish_id": dish_id, "dish": dish_id}))
            elif obj["state"] == "ready" and self.hand is None:
                dish_id = obj["dish"]
                self.hand_base_price = obj.get("base_price", self.menu[dish_id]["price"])
                obj["state"] = "idle"
                obj["dish"] = None
                obj["cook_ticks_left"] = 0
                obj["ready_ticks"] = 0
                self.hand = dish_id
                events.append(("dish_picked", {"stove_id": obj["id"], "dish_id": dish_id, "dish": dish_id}))
            elif obj["state"] == "burned":
                dish_id = obj["dish"]
                obj["state"] = "idle"
                obj["dish"] = None
                obj["cook_ticks_left"] = 0
                obj["ready_ticks"] = 0
                events.append(("dish_discarded", {"stove_id": obj["id"], "dish_id": dish_id, "dish": dish_id}))
        else:
            if self.hand is not None:
                for c in sort_by_id(self.customers):
                    if c["table_id"] == obj["id"] and c["state"] in ("waiting", "ordered"):
                        if c["dish_id"] != self.hand:
                            continue
                        # Serving a reusable orphan dish does not consume the waiting
                        # customer's reserved ingredients; release those IDs/counts.
                        self._release_reservation(c["id"])
                        c["state"] = "eating"
                        c["eat_ticks_left"] = int(round(self.t["eat_s"] * self.tick_hz))
                        p_left = c.get("patience_ticks_left", c.get("patience_ticks", 0))
                        p_max = c.get("patience_max_ticks", int(round(self.t["patience_s"] * self.tick_hz)))
                        c["patience_ratio_served"] = p_left / p_max if p_max > 0 else 1.0
                        if getattr(self, "hand_base_price", None) is not None:
                            c["base_price"] = self.hand_base_price
                        dish_id = self.hand
                        self.hand = None
                        self.hand_base_price = None
                        events.append(("served", {"customer_id": c["id"], "table_id": obj["id"],
                                                  "dish_id": dish_id, "dish": dish_id}))
                        break
        return events

    def _interact(self):
        for kind, obj in self._candidate_interactions():
            events = self._try_interact(kind, obj)
            if events:
                return events
        return []

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / self.tick_hz
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
