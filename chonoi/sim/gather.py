"""Buổi sáng — Lặn & Hái (`gather`). KHUNG: bơi, chặn mép, đồng hồ, cập bến, xuất kho.

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Đã làm sẵn để smoke test chạy được: bơi + tăng/giảm tốc, chặn mép (d không âm), đồng hồ và hết giờ,
cập bến (`interact` trong vùng bến -> `gather_end` reason `docked`), xuất kho, snapshot đầy đủ trường gather.

Phase 1 (PRD mục 13.8, "Gather"):
  Lát 1: bơi + oxy + biên + giỏ
      - oxy: dưới nước (d > surface_depth) trừ 1 tick/tick, mặt nước hồi oxygen_refill_per_tick, kẹp [0, max]
      - ngạt: oxy = 0 và đang dưới nước -> đếm zero_oxy_ticks, đủ choke_interval_ticks thì -1 Máu (choke)
      - Máu về 0 -> ngất (faint, gather_end reason `fainted`, mất toàn bộ giỏ, kho rỗng)
      - sự kiện dive / surface / oxygen_empty / choke / faint
      - giỏ: thứ tự nhặt (LIFO), sức chứa hold_capacity
  Lát 2: hái + bắt cá + cập bến + kho
      - hái nút ở mặt nước (gather, hold_full), nút mọc lại (node_regrown đã có phần đếm ngược)
      - bắt đàn cá bằng `catch` (fish_caught, hold_full, hồi chiêu catch_cd_ticks, chỉ khi dưới nước)
      - cập bến xét TRƯỚC hái (đã có); ghi kho đúng một lần do runner lo
Phase 2: cá bơi, đổi hướng và sinh đàn theo tuning Gather.
"""

import math
from dataclasses import dataclass
from fractions import Fraction

from ..ids import sort_by_id
from ..inventory import Item, hold_to_items
from .monsters import MonsterSystem
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")

_HoldItem = Item


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, day=1):
        t = tuning["gather"]
        self.t = t
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        self.oxygen_max = int(round(t["oxygen_max_s"] * TICK))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp = p.get("hp", t["hp_max"])
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        self.individual_hold = tuning.get("contract_version") in ("1.2", "1.3")
        self.hold = list(scenario.get("hold", []))  # thứ tự nhặt, cuối mảng là mới nhất
        if self.individual_hold:
            freshness = tuning["freshness"]
            self.initial_freshness = Fraction(str(freshness["initial"]))
            self.freshness_decay = Fraction(str(freshness["gather_decay_per_s"])) / tuning["tick_hz"]
            self.spoiled_below = Fraction(str(freshness["spoiled_below"]))
            normalized = []
            for item in self.hold:
                if isinstance(item, Item):
                    normalized.append(item)
                elif isinstance(item, dict):
                    normalized.append(_HoldItem(item["id"], item["kind"], Fraction(str(item["fresh"]))))
                else:
                    # Upgrade legacy fixture kinds into physical inventory at initial freshness.
                    normalized.append(_HoldItem(self.ids.new("I"), item, self.initial_freshness))
            self.hold = normalized
            for item in self.hold:
                ids.reserve(item.id)
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        # Scenario thay thế danh sách mặc định. Fixture cá giữ vị trí cố định.
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        self.random_fish = "fish" not in scenario and scenario.get("random_fish", True)
        initial = t["fish_initial"]
        self.generated_fish = isinstance(initial, int)
        src_fish = scenario.get("fish", [])
        if self.random_fish and not self.generated_fish:
            src_fish = initial
        self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                      "heading_deg": f.get("heading_deg", 0), "age_ticks": 0} for f in src_fish]
        self.fixture_fish_ids = {f["id"] for f in src_fish} if "fish" in scenario else set()
        self.fish_motion = t.get("fish_motion")
        self.fish_spawn_by_tick = {}
        if self.random_fish:
            if self.generated_fish:
                self.fish_motion = {
                    "speed": t["fish_speed"], "turn_every_ticks": t["fish_turn_ticks"],
                    "min_depth": t["bounds"]["d"][0],
                }
            else:
                for spawn in t.get("fish_spawn_schedule", ()):
                    self.fish_spawn_by_tick.setdefault(spawn["tick"], []).append(spawn)
        self.elapsed_ticks = 0
        monster_tuning = t.get("monsters")
        monster_spawns = scenario.get("monsters")
        if monster_spawns is None and monster_tuning:
            monster_spawns = [
                spawn for spawn in monster_tuning.get("spawns", [])
                if spawn.get("day", 1) <= day
            ]
        self.monsters = MonsterSystem(
            monster_tuning or {"species": {}},
            monster_spawns or [],
            t["bounds"],
            tuning["tick_hz"],
        )
        for coll in (self.nodes, self.fish):
            for e in coll:
                ids.reserve(e["id"])
        if self.generated_fish and self.random_fish:
            positions = [(x, depth) for x in t["fish_x"] for depth in t["fish_depths"]]
            initial_rng = self.rng.get("fish_initial")
            for pos in initial_rng.sample(positions, initial):
                self._add_random_fish(pos, initial_rng)
        for monster in self.monsters.monsters:
            ids.reserve(monster["id"])
        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None

    # --- giao diện cho runner -------------------------------------------------
    def inventory_items(self) -> dict | list:
        if self.individual_hold:
            return [item.snapshot() for item in sort_by_id(self.hold, key=lambda item: item.id)]
        return hold_to_items(self.hold)

    def snapshot(self) -> dict:
        return {
            "player": {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.t["hp_max"], "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": [item.snapshot() for item in self.hold] if self.individual_hold else self.hold,
            "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"],
                      "heading_deg": f["heading_deg"], "age_ticks": f["age_ticks"]}
                     for f in sort_by_id(self.fish)],
            "monsters": self.monsters.snapshot(),
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events = []
        self.elapsed_ticks += 1
        invulnerable_at_start = self.invuln_ticks > 0
        # 1. đồng hồ và hàng có sẵn: giảm bộ đếm, nút mọc lại
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))
        if self.individual_hold:
            self._age_hold(events)
        # 2. bơi + chặn mép
        was_surface = self._at_surface()
        self._move(inp)
        is_surface = self._at_surface()
        if was_surface and not is_surface:
            events.append(("dive", {"pos": list(self.pos)}))
        elif not was_surface and is_surface:
            events.append(("surface", {"pos": list(self.pos)}))
        oxygen_events = self._update_oxygen()
        events.extend(oxygen_events)
        if self.done:
            return events
        monster = self.monsters.step(
            self.pos, not invulnerable_at_start and self.invuln_ticks <= 0
        )
        if monster is not None:
            events.extend(self._hit_by_monster(monster))
            if self.done:
                return events
        # 3. interact: bến trước, rồi hái
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            events.extend(self._try_harvest())
        # 4. bắt cá
        if inp.pressed("catch"):
            events.extend(self._try_catch())
        # 5. hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
        else:
            self._tick_fish(events)
        return events

    # --- tiện ích ---------------------------------------------------------------
    def _add_random_fish(self, pos, rng):
        weights = self.t["fish_weights"]
        kind = rng.choices(list(weights), weights=list(weights.values()))[0]
        fish = {"id": self.ids.new("F"), "kind": kind, "pos": list(pos),
                "heading_deg": rng.uniform(0, 360), "age_ticks": 0}
        self.fish.append(fish)
        return fish

    def _tick_fish(self, events):
        motion = self.fish_motion
        for fish in self.fish:
            fish["age_ticks"] += 1
        if motion:
            turn_period = motion["turn_every_ticks"]
            turn_limit = motion.get("max_turn_deg")
            distance = motion["speed"] / TICK
            x_min, x_max = self.t["bounds"]["x"]
            d_min, d_max = motion["min_depth"], self.t["bounds"]["d"][1]
            for fish in sort_by_id(self.fish):
                if fish["id"] in self.fixture_fish_ids:
                    continue
                heading = fish["heading_deg"]
                if fish["age_ticks"] % turn_period == 0:
                    turn_rng = self.rng.get("fish_turn")
                    if turn_limit is None:
                        heading = turn_rng.uniform(0, 360)
                    else:
                        heading += turn_rng.uniform(-turn_limit, turn_limit)
                angle = math.radians(heading)
                x = fish["pos"][0] + distance * math.cos(angle)
                depth = fish["pos"][1] + distance * math.sin(angle)
                if x < x_min or x > x_max:
                    heading = 180 - heading
                if depth < d_min or depth > d_max:
                    heading = -heading
                fish["pos"] = [min(x_max, max(x_min, x)), min(d_max, max(d_min, depth))]
                fish["heading_deg"] = heading % 360
        for spawn in self.fish_spawn_by_tick.get(self.elapsed_ticks, ()):
            fish = {"id": self.ids.new("F"), "kind": spawn["kind"], "pos": list(spawn["pos"]),
                    "heading_deg": spawn["heading_deg"], "age_ticks": 0}
            self.fish.append(fish)
            events.append(("fish_spawned", {"id": fish["id"], "kind": fish["kind"], "pos": fish["pos"]}))
        if self.generated_fish and self.random_fish:
            self._spawn_fish(events)

    def _spawn_fish(self, events):
        if self.elapsed_ticks % self.t["fish_spawn_ticks"] or len(self.fish) >= self.t["fish_max"]:
            return
        clearance = self.t["fish_spawn_clearance"]
        positions = [(x, depth) for x in self.t["fish_spawn_x"] for depth in self.t["fish_spawn_depths"]
                     if all(math.dist((x, depth), fish["pos"]) > clearance for fish in self.fish)]
        if positions:
            spawn_rng = self.rng.get("fish_spawn")
            fish = self._add_random_fish(spawn_rng.choice(positions), spawn_rng)
            events.append(("fish_spawned", {"id": fish["id"], "kind": fish["kind"], "pos": fish["pos"]}))

    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _nearest(self, entities, radius):
        nearest = None
        nearest_distance = math.inf
        for entity in sort_by_id(entities):
            distance = math.dist(self.pos, entity["pos"])
            if distance <= radius and distance < nearest_distance:
                nearest = entity
                nearest_distance = distance
        return nearest

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("gather_end", {"reason": reason, "inventory": {"items": self.inventory_items()}}))

    def _age_hold(self, events):
        for item in sort_by_id(self.hold, key=lambda item: item.id):
            before = item.fresh
            item.fresh = max(Fraction(0), before - self.freshness_decay)
            if item.fresh < self.spoiled_below <= before:
                events.append(("spoiled", {"item_id": item.id, "kind": item.kind, "location": "hold"}))

    def _push_hold(self, kind, amount=1):
        room = self.t["hold_capacity"] - len(self.hold)
        accepted = min(max(0, room), amount)
        if self.individual_hold:
            self.hold.extend(_HoldItem(self.ids.new("I"), kind, self.initial_freshness)
                             for _ in range(accepted))
        else:
            self.hold.extend([kind] * accepted)
        return accepted

    def _update_oxygen(self):
        events = []
        if self._at_surface():
            before = self.oxygen_ticks
            self.oxygen_ticks = min(self.oxygen_max,
                                    self.oxygen_ticks + int(self.t["oxygen_refill_per_tick"]))
            if before == 0 and self.oxygen_ticks > 0:
                self.zero_oxy_ticks = 0
            return events

        if self.oxygen_ticks > 0:
            self.oxygen_ticks -= 1
            if self.oxygen_ticks == 0:
                events.append(("oxygen_empty", {"pos": list(self.pos)}))
                self.zero_oxy_ticks = 0
            return events

        self.zero_oxy_ticks += 1
        if self.zero_oxy_ticks >= int(self.t["choke_interval_ticks"]):
            self.zero_oxy_ticks = 0
            if self.invuln_ticks <= 0:
                self.hp = max(0, self.hp - 1)
                self.invuln_ticks = int(self.t["choke_interval_ticks"])
                events.append(("choke", {"hp": self.hp, "pos": list(self.pos)}))
                if self.hp <= 0:
                    lost = self._lose_all_hold()
                    events.append(("faint", {"cause": "choke", "lost": lost,
                                             "hp": 0, "pos": list(self.pos)}))
                    self._finish("fainted", events)
        return events

    def _hit_by_monster(self, monster):
        monster_config = self.t["monsters"]
        lost_count = int(len(self.hold) * monster_config["loss_ratio"])
        lost = [self.hold.pop() for _ in range(lost_count)]
        self.hp = max(0, self.hp - 1)
        self.invuln_ticks = int(monster_config["invuln_ticks"])
        self.monsters.start_recoil(monster, self.pos)
        events = [("monster_hit", {
            "monster_id": monster["id"], "hp": self.hp, "lost": lost,
            "pos": list(self.pos),
        })]
        if self.hp == 0:
            faint_lost = self._lose_all_hold()
            events.append(("faint", {
                "cause": "monster", "lost": faint_lost, "hp": 0, "pos": list(self.pos),
            }))
            self._finish("fainted", events)
        return events

    def _lose_all_hold(self):
        lost = []
        while self.hold:
            lost.append(self.hold.pop())
        return lost

    def _try_harvest(self):
        events = []
        if not self._at_surface():
            return events
        ready = (node for node in self.nodes if node["regrow_ticks"] == 0)
        node = self._nearest(ready, self.t["interact_radius"])
        if node is None:
            return events
        amount = int(self.t["node_yield"])
        accepted = self._push_hold(node["kind"], amount)
        if accepted > 0:
            node["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
            events.append(("gather", {"node_id": node["id"], "kind": node["kind"],
                                      "item": node["kind"], "yield": accepted,
                                      "hold_count": len(self.hold)}))
        if accepted < amount or len(self.hold) >= self.t["hold_capacity"]:
            events.append(("hold_full", {"hold_count": len(self.hold),
                                         "hold_capacity": self.t["hold_capacity"]}))
        return events

    def _try_catch(self):
        events = []
        if self.catch_cd_ticks > 0 or self._at_surface():
            return events
        if len(self.hold) >= self.t["hold_capacity"]:
            events.append(("hold_full", {"hold_count": len(self.hold),
                                         "hold_capacity": self.t["hold_capacity"]}))
            return events
        fish = self._nearest(self.fish, self.t["catch_radius"])
        if fish is None:
            return events
        amount = int(self.t["fish_yield"][fish["kind"]])
        if len(self.hold) + amount > self.t["hold_capacity"]:
            events.append(("hold_full", {"hold_count": len(self.hold),
                                         "hold_capacity": self.t["hold_capacity"]}))
            return events
        accepted = self._push_hold(fish["kind"], amount)
        if accepted > 0:
            self.fish.remove(fish)
            self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
            events.append(("fish_caught", {"fish_id": fish["id"], "kind": fish["kind"],
                                           "item": fish["kind"], "yield": accepted,
                                           "hold_count": len(self.hold)}))
        if accepted < amount or len(self.hold) >= self.t["hold_capacity"]:
            events.append(("hold_full", {"hold_count": len(self.hold),
                                         "hold_capacity": self.t["hold_capacity"]}))
        return events

    def _move(self, inp):
        speed = self.t["swim_speed"]
        mx, md = inp.move
        self.vel = ramp_velocity(self, (mx * speed, md * speed), int(self.t["ramp_max_ticks"]))
        if (mx, md) != (0.0, 0.0):
            self.heading = math.degrees(math.atan2(md, mx)) % 360
        b = self.t["bounds"]
        for i, axis in enumerate(AXES):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i] = lo
                self.vel[i] = max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i] = hi
                self.vel[i] = min(0.0, self.vel[i])
