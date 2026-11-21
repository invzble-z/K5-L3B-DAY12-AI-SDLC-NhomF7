"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

KHUNG: kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ.
TODO(nhóm): bổ sung kiểm mâu thuẫn mức luật mà nhóm cần (khách giữ chỗ quá kho, đơn assigned
phải có đúng một món, khách eating thiếu giá/tip...) — xem PRD-0 mục D và 'Mâu thuẫn -> mã 2'.
"""

import json

from .errors import BadInput
from .inventory import KINDS_P1, validate_item_objects, validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "monsters", "random_fish", "time_left_ticks"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks"}
NODE_KINDS = ("bong_dien_dien", "bong_sung")
FISH_KINDS = ("ca_linh", "ca_loc")
CUSTOMER_KEYS = {"id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left",
                 "eat_ticks_left", "order_status", "reserved", "base_price", "tip"}
QUAN_PLAYER_KEYS = {"pos", "vel"}
QUAN_KEYS = {"player", "stock", "hand", "stoves", "tables", "customers", "random_customers",
             "reputation", "time_left_ticks"}


def _check_ids(name, arr):
    if not isinstance(arr, list):
        raise BadInput(f"{name} phải là mảng")
    seen = set()
    for e in arr:
        if not isinstance(e, dict) or not isinstance(e.get("id"), str) or not e["id"]:
            raise BadInput(f"{name}: mỗi phần tử cần id (chuỗi khác rỗng)")
        if e["id"] in seen:
            raise BadInput(f"{name}: id trùng {e['id']}")
        seen.add(e["id"])


def load_scenario(path, mode: str, tuning: dict) -> dict:
    if path is None:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được scenario {path}: {e}")
    if not isinstance(data, dict) or not set(data) <= {"gather", "quan", "day"}:
        raise BadInput("scenario chỉ được có khối 'gather', 'quan' hoặc 'day'")
    if mode == "day":
        if set(data) - {"gather", "quan", "day"}:
            raise BadInput("khối sai mode: chạy --mode day chỉ nhận 'gather', 'quan' và 'day'")
        out = {}
        if "day" in data:
            if not isinstance(data["day"], dict):
                raise BadInput("khối day phải là object")
            out["day"] = data["day"]
        for day_mode in ("gather", "quan"):
            if day_mode not in data:
                continue
            block = data[day_mode]
            if not isinstance(block, dict):
                raise BadInput(f"khối {day_mode} phải là object")
            allowed = GATHER_KEYS if day_mode == "gather" else QUAN_KEYS
            extra = set(block) - allowed
            if extra:
                raise BadInput(f"trường lạ/chưa hỗ trợ trong {day_mode}: {sorted(extra)}")
            dur = int(round(tuning[day_mode]["duration_s"] * 60))
            if "time_left_ticks" in block:
                t = block["time_left_ticks"]
                if isinstance(t, bool) or not isinstance(t, int) or not (1 <= t <= dur):
                    raise BadInput(f"time_left_ticks phải là số nguyên trong [1, {dur}]")
            if day_mode == "gather":
                _validate_gather(block, tuning)
            else:
                _validate_quan(block, tuning)
            out[day_mode] = block
        return out
    if set(data) - {mode}:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối '{mode}'")
    block = data.get(mode, {})
    if not isinstance(block, dict):
        raise BadInput(f"khối {mode} phải là object")
    allowed = GATHER_KEYS if mode == "gather" else QUAN_KEYS
    extra = set(block) - allowed
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong {mode}: {sorted(extra)}")
    dur = int(round(tuning[mode]["duration_s"] * 60))
    if "time_left_ticks" in block:
        t = block["time_left_ticks"]
        if isinstance(t, bool) or not isinstance(t, int) or not (1 <= t <= dur):
            raise BadInput(f"time_left_ticks phải là số nguyên trong [1, {dur}]")
    if mode == "gather":
        _validate_gather(block, tuning)
    else:
        _validate_quan(block, tuning)
    return block


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _nonneg_int(name, v):
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise BadInput(f"{name} phải là số nguyên không âm")


def _pos(name, pos, bounds, axes=("x", "d")):
    if not (isinstance(pos, list) and len(pos) == 2 and all(_num(c) for c in pos)):
        raise BadInput(f"{name} phải là [{axes[0]}, {axes[1]}]")
    for c, axis in zip(pos, axes):
        lo, hi = bounds[axis]
        if not (lo <= c <= hi):
            raise BadInput(f"{name} nằm ngoài vùng nước ({axis} ∈ [{lo}, {hi}])")


def _validate_gather(b, tuning):
    g = tuning["gather"]
    bounds = g["bounds"]
    for arr in ("nodes", "fish"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "random_fish" in b and not isinstance(b["random_fish"], bool):
        raise BadInput("random_fish phải là boolean")
    if "hold" in b:
        h = b["hold"]
        if not isinstance(h, list):
            raise BadInput("hold phải là mảng nguyên liệu hợp lệ")
        if tuning.get("contract_version") in ("1.2", "1.3"):
            if h and isinstance(h[0], dict):
                validate_item_objects(h)
            elif any(kind not in KINDS_P1 for kind in h):
                raise BadInput("hold phải là mảng Item hoặc loại nguyên liệu hợp lệ")
        elif any(k not in KINDS_P1 for k in h):
            raise BadInput("hold phải là mảng id nguyên liệu hợp lệ")
        if len(h) > g["hold_capacity"]:
            raise BadInput("hold vượt sức chứa")
    p = b.get("player", {})
    if not isinstance(p, dict):
        raise BadInput("player phải là object")
    extra = set(p) - GATHER_PLAYER_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong gather.player: {sorted(extra)}")
    if "pos" in p:
        _pos("player.pos", p["pos"], bounds)
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, d]")
    if "heading_deg" in p and not _num(p["heading_deg"]):
        raise BadInput("player.heading_deg phải là số")
    for key in ("invuln_ticks", "catch_cd_ticks", "zero_oxy_ticks", "oxygen_ticks", "hp"):
        if key in p:
            _nonneg_int(f"player.{key}", p[key])
    omax = int(round(g["oxygen_max_s"] * 60))
    if "oxygen_ticks" in p and p["oxygen_ticks"] > omax:
        raise BadInput("player.oxygen_ticks vượt oxy tối đa")
    if "hp" in p and not (1 <= p["hp"] <= g["hp_max"]):
        raise BadInput("player.hp phải trong [1, hp_max]")
    if "zero_oxy_ticks" in p:
        pos = p.get("pos", g["start_pos"])
        oxy = p.get("oxygen_ticks", omax)
        if p["zero_oxy_ticks"] > 59:
            raise BadInput("player.zero_oxy_ticks phải trong [0, 59]")
        if p["zero_oxy_ticks"] > 0 and not (oxy == 0 and pos[1] > g["surface_depth"]):
            raise BadInput("player.zero_oxy_ticks > 0 chỉ khi oxy = 0 và đang dưới nước")
    for n in b.get("nodes", []):
        if n.get("kind") not in NODE_KINDS:
            raise BadInput(f"nodes.{n['id']}: kind phải là một trong {NODE_KINDS}")
        _pos(f"nodes.{n['id']}.pos", n.get("pos"), bounds)
        if n["pos"][1] != 0:
            raise BadInput(f"nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
        if "regrow_ticks" in n:
            _nonneg_int(f"nodes.{n['id']}.regrow_ticks", n["regrow_ticks"])
    for f in b.get("fish", []):
        if f.get("kind") not in FISH_KINDS:
            raise BadInput(f"fish.{f['id']}: kind phải là một trong {FISH_KINDS}")
        _pos(f"fish.{f['id']}.pos", f.get("pos"), bounds)
        if f["pos"][1] <= g["surface_depth"]:
            raise BadInput(f"fish.{f['id']}: đàn cá phải ở dưới nước")
        if "heading_deg" in f and not _num(f["heading_deg"]):
            raise BadInput(f"fish.{f['id']}.heading_deg phải là số")
    if "monsters" in b:
        _check_ids("monsters", b["monsters"])
        species_config = g.get("monsters", {}).get("species", {})
        for monster in b["monsters"]:
            extra = set(monster) - {"id", "species", "pos", "waypoints"}
            if extra:
                raise BadInput(f"monsters.{monster['id']}: trường lạ: {sorted(extra)}")
            species = monster.get("species")
            if species not in species_config:
                raise BadInput(f"monsters.{monster['id']}.species không hợp lệ")
            depths = species_config[species]["depths"]
            if "pos" in monster:
                _pos(f"monsters.{monster['id']}.pos", monster["pos"], bounds)
                if not depths[0] <= monster["pos"][1] <= depths[1]:
                    raise BadInput(f"monsters.{monster['id']}.pos nằm ngoài dải độ sâu của loài")
            waypoints = monster.get("waypoints")
            if not isinstance(waypoints, list) or len(waypoints) != 2:
                raise BadInput(f"monsters.{monster['id']}.waypoints phải có đúng 2 điểm")
            for index, waypoint in enumerate(waypoints):
                _pos(f"monsters.{monster['id']}.waypoints[{index}]", waypoint, bounds)
                if not depths[0] <= waypoint[1] <= depths[1]:
                    raise BadInput(f"monsters.{monster['id']}.waypoints nằm ngoài dải độ sâu của loài")


def _validate_quan(b, tuning):
    if "random_customers" in b and not isinstance(b["random_customers"], bool):
        raise BadInput("random_customers phải là boolean")
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    individual = tuning.get("contract_version") in ("1.2", "1.3")
    stock_items = None
    if "stock" in b:
        if individual:
            if not isinstance(b["stock"], list):
                raise BadInput("kho quán v1.2/v1.3 phải là mảng Item")
            stock_items = validate_item_objects(b["stock"])
        else:
            if not isinstance(b["stock"], dict):
                raise BadInput("kho quán v1.0/v1.1 phải là object đếm")
            validate_items(b["stock"])
    if "hand" in b and b["hand"] is not None and b["hand"] not in tuning["menu"]:
        raise BadInput("quan.hand phải là dish_id hợp lệ")
    if "reputation" in b:
        q = tuning["quan"]
        if not _num(b["reputation"]) or not (q["reputation_min"] <= b["reputation"] <= q["reputation_max"]):
            raise BadInput("quan.reputation nằm ngoài dải cho phép")
    p = b.get("player", {})
    if not isinstance(p, dict) or set(p) - QUAN_PLAYER_KEYS:
        raise BadInput("quan.player chỉ có pos và vel")
    qb = tuning["quan"]["bounds"]
    if "pos" in p:
        _pos("player.pos", p["pos"], qb, axes=("x", "z"))
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, z]")
    table_ids = [c.get("table_id") for c in b.get("customers", [])]
    known = {t["id"] for t in tuning["quan"]["tables"]} | {t.get("id") for t in b.get("tables", [])}
    menu = tuning["menu"]
    stock = b.get("stock", [] if individual else {})
    reserved_totals = {}
    held_ids = set()
    item_by_id = {item.id: item for item in (stock_items or [])}
    for c in b.get("customers", []):
        extra = set(c) - CUSTOMER_KEYS
        if extra:
            raise BadInput(f"customers.{c['id']}: trường lạ/chưa hỗ trợ: {sorted(extra)}")
        if not isinstance(c.get("table_id"), str) or c["table_id"] not in known:
            raise BadInput(f"customers.{c['id']}: table_id phải là bàn có thật")
        dish_id = c.get("dish_id")
        if not isinstance(dish_id, str) or dish_id not in menu:
            raise BadInput(f"customers.{c['id']}: dish_id phải là món có trong menu")
        state = c.get("state", "waiting")
        if state not in ("waiting", "ordered", "eating"):
            raise BadInput(f"customers.{c['id']}: state không hợp lệ")
        for key in ("order_tick", "patience_ticks_left", "eat_ticks_left"):
            if key in c:
                _nonneg_int(f"customers.{c['id']}.{key}", c[key])
        recipe = menu[dish_id]["recipe"]
        reserved = c.get("reserved", [] if individual else
                         ({} if state in ("ordered", "eating") else recipe))
        if individual:
            if state in ("ordered", "eating"):
                if reserved not in ([], {}):
                    raise BadInput(f"customers.{c['id']}: khách đã nấu không giữ nguyên liệu thô")
                continue
            if "reserved" in c:
                if not isinstance(reserved, list):
                    raise BadInput(f"customers.{c['id']}.reserved phải là mảng ID Item")
                if len(reserved) != len(set(reserved)):
                    raise BadInput(f"customers.{c['id']}.reserved có ID trùng")
                counts = {}
                for item_id in reserved:
                    item = item_by_id.get(item_id)
                    if item is None:
                        raise BadInput(f"customers.{c['id']}.reserved tham chiếu ID không có trong kho")
                    if item_id in held_ids:
                        raise BadInput("một id nguyên liệu không thể được giữ bởi nhiều khách")
                    held_ids.add(item_id)
                    if item.fresh < tuning.get("freshness", {}).get("spoiled_below", 30):
                        raise BadInput(f"customers.{c['id']}.reserved chứa nguyên liệu đã ươn")
                    counts[item.kind] = counts.get(item.kind, 0) + 1
                if counts != recipe:
                    raise BadInput(f"customers.{c['id']}.reserved không khớp recipe")
            else:
                for kind, amount in recipe.items():
                    reserved_totals[kind] = reserved_totals.get(kind, 0) + amount
        else:
            if not isinstance(reserved, dict):
                raise BadInput(f"customers.{c['id']}.reserved phải là object")
            try:
                reserved = validate_items(reserved)
            except BadInput as e:
                raise BadInput(f"customers.{c['id']}.reserved: {e}")
            if state in ("ordered", "eating") and reserved:
                raise BadInput(f"customers.{c['id']}: khách đã nấu không giữ nguyên liệu thô")
            for kind, amount in reserved.items():
                reserved_totals[kind] = reserved_totals.get(kind, 0) + amount
    if "stock" in b:
        if individual:
            available = {}
            spoiled_below = tuning.get("freshness", {}).get("spoiled_below", 30)
            for item in stock_items:
                if item.id not in held_ids and item.fresh >= spoiled_below:
                    available[item.kind] = available.get(item.kind, 0) + 1
            for kind, amount in reserved_totals.items():
                if available.get(kind, 0) < amount:
                    raise BadInput("nguyên liệu giữ chỗ vượt kho cá thể")
        else:
            for kind, amount in reserved_totals.items():
                if stock.get(kind, 0) < amount:
                    raise BadInput("nguyên liệu giữ chỗ vượt kho")
    if len(table_ids) != len(set(table_ids)):
        raise BadInput("hai khách cùng bàn")
