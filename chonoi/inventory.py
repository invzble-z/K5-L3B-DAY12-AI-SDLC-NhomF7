"""File kho: hỗ trợ cả kho đếm v1.0/v1.1 và kho cá thể v1.2 (Contract G & Phase 3).

- v1.0 / v1.1: {"items": {id: số nguyên >= 0}}
- v1.2: {"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}, ...]}

Đọc: từ chối sai schema / id lạ / id trùng / fresh ngoài [0, 100] (BadInput -> mã 2).
Ghi: qua file tạm cùng thư mục rồi thay thế (nguyên tử), byte-ổn-định, sắp theo id.
"""

from fractions import Fraction
import json
import math
import os
import tempfile

from .errors import BadInput
from .ids import sort_by_id

KINDS_P1 = ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")


class Item:
    """Đại diện nguyên liệu cá thể trong kho / giỏ (Phase 3)."""

    id: str
    kind: str
    fresh: Fraction

    def __init__(self, id: str, kind: str, fresh):
        if not isinstance(id, str) or not id:
            raise BadInput("Item id phải là chuỗi khác rỗng")
        if kind not in KINDS_P1:
            raise BadInput(f"nguyên liệu lạ: {kind}")
        if isinstance(fresh, bool):
            raise BadInput(f"fresh không hợp lệ: {fresh!r}")
        if isinstance(fresh, (int, float)):
            if not math.isfinite(fresh) or fresh < 0 or fresh > 100:
                raise BadInput(f"fresh ngoài miền [0, 100]: {fresh}")
            fresh_f = Fraction(str(fresh))
        elif isinstance(fresh, str):
            try:
                fresh_f = Fraction(fresh)
            except (ValueError, ZeroDivisionError):
                raise BadInput(f"fresh không hợp lệ: {fresh}")
            if fresh_f < 0 or fresh_f > 100:
                raise BadInput(f"fresh ngoài miền [0, 100]: {fresh}")
        elif isinstance(fresh, Fraction):
            if fresh < 0 or fresh > 100:
                raise BadInput(f"fresh ngoài miền [0, 100]: {fresh}")
            fresh_f = fresh
        else:
            raise BadInput(f"fresh không hợp lệ: {fresh!r}")
        self.id = id
        self.kind = kind
        self.fresh = fresh_f

    def __getitem__(self, key):
        if key == "id":
            return self.id
        elif key == "kind":
            return self.kind
        elif key == "fresh":
            return float(self.fresh)
        raise KeyError(key)

    def snapshot(self) -> dict:
        return {"id": self.id, "kind": self.kind, "fresh": float(self.fresh)}

    def to_dict(self) -> dict:
        val = float(self.fresh)
        if val.is_integer():
            val = int(val)
        return {"id": self.id, "kind": self.kind, "fresh": val}

    def __repr__(self):
        return f"Item(id={self.id!r}, kind={self.kind!r}, fresh={self.fresh})"

    def __eq__(self, other):
        if isinstance(other, Item):
            return self.id == other.id and self.kind == other.kind and self.fresh == other.fresh
        elif isinstance(other, dict):
            return self.id == other.get("id") and self.kind == other.get("kind") and float(self.fresh) == other.get("fresh")
        return False


def get_contract_version() -> str:
    try:
        from .contract import load_contract
        return load_contract().get("contract_version", "1.1")
    except Exception:
        return "1.1"


def validate_items(items, kinds=KINDS_P1):
    if not isinstance(items, dict):
        raise BadInput("items phải là object")
    out = {}
    for k, v in items.items():
        if k not in kinds:
            raise BadInput(f"nguyên liệu lạ: {k}")
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise BadInput(f"số lượng không hợp lệ cho {k}: {v!r}")
        if v > 0:
            out[k] = v
    return out


def validate_item_objects(items, kinds=KINDS_P1) -> list:
    if not isinstance(items, list):
        raise BadInput("items phải là mảng")
    seen = set()
    out = []
    for i, e in enumerate(items):
        if isinstance(e, Item):
            item_id, item_kind, item_fresh = e.id, e.kind, e.fresh
        elif isinstance(e, dict):
            allowed = {"id", "kind", "fresh"}
            if set(e.keys()) != allowed:
                raise BadInput(f"item {i} sai schema, cần đúng các khóa: {sorted(allowed)}")
            item_id, item_kind, item_fresh = e["id"], e["kind"], e["fresh"]
        else:
            raise BadInput(f"item {i} phải là object")
        if item_id in seen:
            raise BadInput(f"id trùng: {item_id}")
        seen.add(item_id)
        out.append(Item(item_id, item_kind, item_fresh))
    return sort_by_id(out, key=lambda x: x.id)


def read_inventory(path: str, kinds=KINDS_P1, version=None):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    ver = version if version is not None else get_contract_version()
    if version in ("1.2", "1.3") or (version is None and ver in ("1.2", "1.3")):
        if not isinstance(data["items"], list):
            raise BadInput(f"file kho v{ver} phải là mảng cá thể")
        return validate_item_objects(data["items"], kinds)
    else:
        if not isinstance(data["items"], dict):
            raise BadInput("file kho v1.0/v1.1 phải là object đếm")
        return validate_items(data["items"], kinds)


def read_inventory_or_empty(path: str, kinds=KINDS_P1, version=None):
    """Read an existing inventory, or return an empty one when the file is absent."""
    if not os.path.exists(path):
        ver = version if version is not None else get_contract_version()
        return [] if ver in ("1.2", "1.3") else {}
    return read_inventory(path, kinds, version=version)


def read_inventory_for_mode(mode: str, inventory_path=None, kinds=KINDS_P1, version=None):
    """Nạp kho chỉ định hoặc inventory.json mặc định cho quan/day."""
    path = inventory_path
    if path is None and mode in ("quan", "day") and os.path.exists("inventory.json"):
        path = "inventory.json"
    if path is None:
        return None
    return read_inventory(path, kinds, version=version)


def merge_items(*collections):
    """Sum item counts across inventories and return keys in stable order, or merge individual item lists."""
    if not collections:
        return {}
    has_list = any(isinstance(c, list) for c in collections)
    if has_list:
        merged = []
        for c in collections:
            if isinstance(c, list):
                merged.extend(c)
        return sort_by_id(merged, key=lambda x: x.id if isinstance(x, Item) else x["id"])
    totals = {}
    for items in collections:
        if isinstance(items, dict):
            for kind, amount in items.items():
                totals[kind] = totals.get(kind, 0) + amount
    return {kind: totals[kind] for kind in sorted(totals) if totals[kind] > 0}


def hold_to_items(hold: list, ids=None, version=None):
    """Khoang -> object đếm (v1.0/1.1) hoặc mảng cá thể Item (v1.2)."""
    ver = version if version is not None else get_contract_version()
    if ver in ("1.2", "1.3") and ids is not None:
        out = []
        for k in hold:
            if isinstance(k, Item):
                out.append(k)
            elif isinstance(k, dict):
                out.append(Item(k["id"], k["kind"], k["fresh"]))
            else:
                out.append(Item(ids.new("I"), k, Fraction(100)))
        return sort_by_id(out, key=lambda x: x.id)
    counts = {}
    for k in hold:
        kind = k.kind if isinstance(k, Item) else (k["kind"] if isinstance(k, dict) else k)
        counts[kind] = counts.get(kind, 0) + 1
    return {k: counts[k] for k in sorted(counts)}


def write_inventory(path: str, items, version=None):
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            if isinstance(items, list):
                sorted_items = sort_by_id(items, key=lambda x: x.id if isinstance(x, Item) else x["id"])
                serialized = [item.to_dict() if isinstance(item, Item) else item for item in sorted_items]
                json.dump({"items": serialized}, f, ensure_ascii=False, separators=(",", ":"))
            elif isinstance(items, dict):
                items_dict = {k: items[k] for k in sorted(items) if items[k] > 0}
                json.dump({"items": items_dict}, f, ensure_ascii=False, separators=(",", ":"))
            else:
                raise BadInput("items phải là dict hoặc list")
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
