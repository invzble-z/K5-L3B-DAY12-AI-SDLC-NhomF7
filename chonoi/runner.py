"""Vòng tick (Contract B, mô hình tick). KHUNG — thường không cần sửa.

Thứ tự ghi: snapshot tick 0 -> với mỗi bước: sự kiện (theo thứ tự xử lý) rồi snapshot (nếu tới lượt
hoặc buổi kết thúc) -> dòng 'end'. Mỗi tick tối đa một snapshot.

`Session` là API bước tick gọn dùng chung cho headless (`run`) và cửa sổ chơi trực tiếp (`chonoi.live`):
cả hai chạy CÙNG một lớp sim, không nhân đôi logic.
"""

import math

from .ids import IdAllocator
from .inputs import InputPlayer, BUTTONS_V10, BUTTONS_V11
from .inventory import merge_items, read_inventory_or_empty, write_inventory
from .jsonl import JsonlWriter
from .rng import Streams
from .sim.gather import GatherSim
from .sim.quan import QuanSim
from .sim.day import DaySim


def build_sim(mode, tuning, scenario, seed, inventory=None, days=None):
    streams, ids = Streams(seed), IdAllocator()
    if isinstance(inventory, list):
        for item in inventory:
            ids.reserve(item.id if hasattr(item, "id") else item["id"])
    if mode == "gather":
        return GatherSim(tuning, scenario, streams, ids)
    if mode == "quan":
        return QuanSim(tuning, scenario, streams, ids, inventory=inventory)
    if mode == "day":
        return DaySim(tuning, scenario, streams, ids, inventory=inventory, days=days or 1)
    raise ValueError(f"mode không hỗ trợ: {mode}")


def _common(sim, tick, sim_tick, phase_tick, tuning, state):
    mult = tuning["score"]["reputation_multiplier"]
    return {
        "type": "snapshot", "tick": tick, "sim_tick": sim_tick, "mode": sim.mode, "phase": sim.phase,
        "phase_tick": phase_tick, "state": state, "time_left_ticks": sim.time_left_ticks,
        "money": sim.money, "earned": sim.earned, "reputation": sim.reputation,
        "score": sim.earned + mult * math.floor(sim.reputation),
    }


class Session:
    """Một lượt chơi: dựng sim, bước từng tick, lấy snapshot / dòng end."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, days=None):
        self.mode = mode
        self.tuning = tuning
        self.sim = build_sim(mode, tuning, scenario, seed, inventory, days=days)
        self.tick = 0

    @property
    def done(self) -> bool:
        return self.sim.done

    def snapshot(self) -> dict:
        if self.mode == "day":
            state = "paused" if getattr(self.sim, "state", None) == "paused" else ("finished" if self.sim.done else "running")
        else:
            state = "finished" if self.sim.done else "playing"
        s = _common(self.sim, self.tick, getattr(self.sim, "sim_tick", self.tick),
                    getattr(self.sim, "phase_tick", self.tick), self.tuning, state)
        s.update(self.sim.snapshot())
        return s

    def step(self, inp) -> list:
        """Chạy một bước với `inp` (chonoi.inputs.InputState); trả các dòng event (tick = k + 1)."""
        events = self.sim.step(inp)
        self.tick += 1
        rows = []
        for item in events:
            if len(item) == 4:
                name, data, event_phase, event_day = item
            elif len(item) == 3:
                name, data, event_phase = item
                event_day = getattr(self.sim, "day", None)
            else:
                name, data = item
                event_phase = getattr(self.sim, "phase", None)
                event_day = getattr(self.sim, "day", None)
            row = {"type": "event", "tick": self.tick, "phase": event_phase,
                   "name": name, "data": data}
            if self.mode == "day":
                row["day"] = event_day if event_day is not None else getattr(self.sim, "day", 1)
            rows.append(row)
        return rows

    def end_row(self) -> dict:
        sim = self.sim
        sim_tick = getattr(sim, "sim_tick", self.tick)
        score = _common(sim, self.tick, sim_tick, getattr(sim, "phase_tick", self.tick),
                        self.tuning, "")["score"]
        row = {"type": "end", "ticks": self.tick, "sim_tick": sim_tick, "mode": sim.mode,
               "state": "finished" if sim.done else ("running" if self.mode == "day" else "playing"),
               "reason": sim.reason if sim.done else "tick_limit",
               "money": sim.money, "earned": sim.earned, "reputation": sim.reputation, "score": score}
        if self.mode == "day":
            row["days_completed"] = getattr(sim, "days_completed", 0)
        return row

    def write_inventory_if_done(self, inventory_out, inventory_base=None):
        """Persist the run's held items on top of the inventory present at run start."""
        if self.mode == "gather" and self.sim.done and inventory_out:
            write_inventory(inventory_out, merge_items(inventory_base or {}, self.sim.inventory_items()))
        elif self.mode == "day" and self.sim.done and inventory_out:
            write_inventory(inventory_out, self.sim.inventory_items())


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every, inventory=None, inventory_out=None, days=None):
    inventory_base = read_inventory_or_empty(inventory_out) if mode in ("gather", "day") and inventory_out else {}
    id_seed_inventory = inventory_base if mode == "gather" and inventory_out else inventory
    sess = Session(mode, tuning, scenario, seed, id_seed_inventory, days=days)
    player = InputPlayer(frames, buttons=BUTTONS_V11 if mode == "day" else BUTTONS_V10)
    w = JsonlWriter(out_path)
    try:
        w.write(sess.snapshot())  # tick 0: sau khi dựng scenario, trước mọi input
        last_snapped = 0
        while sess.tick < ticks and not sess.done:
            inp = player.advance(sess.tick)  # bước k đọc input có tick == k
            rows = sess.step(inp)
            if mode in ("gather", "day") and inventory_out:
                if any(row["name"] in {"gather", "fish_caught", "faint", "gather_end"} for row in rows):
                    items = (sess.sim.inventory_items() if mode == "day"
                             else merge_items(inventory_base, sess.sim.inventory_items()))
                    write_inventory(inventory_out, items)
            for row in rows:
                w.write(row)
            if sess.tick % snapshot_every == 0 or sess.done:
                w.write(sess.snapshot())
                last_snapped = sess.tick
        if last_snapped != sess.tick:
            w.write(sess.snapshot())
        w.write(sess.end_row())
    finally:
        w.close()
    sess.write_inventory_if_done(inventory_out, inventory_base)
    return sess.sim
