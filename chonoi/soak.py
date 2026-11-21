"""Run a deterministic, input-driven DaySim soak without the browser UI.

Example: ``python -m chonoi.soak --seed 7 --days 10 --out soak.json``.
"""

import argparse
from copy import deepcopy
import json
import math
import sys
import time

from .contract import load_contract
from .errors import BadInput
from .inputs import InputState
from .runner import Session


def _tuning_for_days(tuning, days):
    """Copy tuning and expand the configured day-plan cycle for the requested run."""
    expanded = deepcopy(tuning)
    plans = expanded.get("day_plan")
    if isinstance(plans, dict) and plans:
        base = []
        day = 1
        while str(day) in plans or day in plans:
            base.append(deepcopy(plans.get(str(day), plans.get(day))))
            day += 1
        if not base:
            return expanded
        expanded["day_plan"] = {
            str(day): deepcopy(base[(day - 1) % len(base)]) for day in range(1, days + 1)
        }
    elif isinstance(plans, list) and plans:
        by_day = {plan.get("day"): plan for plan in plans if isinstance(plan, dict)}
        base = [deepcopy(by_day[day]) for day in range(1, max(by_day, default=0) + 1) if day in by_day]
        if base:
            expanded["day_plan"] = [
                {**deepcopy(base[(day - 1) % len(base)]), "day": day}
                for day in range(1, days + 1)
            ]
    return expanded


def _integer(name, minimum=None):
    def parse(value):
        try:
            result = int(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"{name} phải là số nguyên") from exc
        if minimum is not None and result < minimum:
            raise argparse.ArgumentTypeError(f"{name} phải >= {minimum}")
        return result
    return parse


def run_soak(seed, days, out_path, tuning=None, scenario=None):
    """Run the real DaySim; optional tuning is only an injectable test seam."""
    tuning = _tuning_for_days(tuning if tuning is not None else load_contract()["tuning"], days)
    session_scenario = scenario if scenario is not None else {
        "day": {"days": days}, "gather": {}, "quan": {}
    }
    session = Session("day", tuning, session_scenario,
                      seed=seed, days=days)
    sim = session.sim
    gather_triggered = set()
    shop_triggered = set()
    results = []
    earned_at_last_day = 0
    crashes = 0
    diagnostics = []
    started = time.perf_counter()
    tick_hz = tuning["tick_hz"]
    quan_max = int(round(tuning["quan"]["duration_s"] * tick_hz))
    gather_max = int(round(tuning["gather"]["duration_s"] * tick_hz))
    shop_max = int(tuning.get("shop", {}).get("max_ticks", 600))
    max_ticks = days * (gather_max + quan_max + shop_max + 8)

    while not sim.done and session.tick < max_ticks:
        edges = set()
        if sim.phase == "gather" and sim.day not in gather_triggered:
            edges.add("interact")
            gather_triggered.add(sim.day)
        elif sim.phase == "shop" and sim.day not in shop_triggered:
            edges.add("shop_done")
            shop_triggered.add(sim.day)
        try:
            rows = session.step(InputState((0.0, 0.0), {}, edges))
        except Exception as exc:  # Report a real runtime crash and leave partial evidence.
            crashes += 1
            diagnostics.append({"day": sim.day, "error": f"{type(exc).__name__}: {exc}"})
            break
        if sim.days_completed > len(results):
            completed_day = len(results) + 1
            daily_earned = sim.earned - earned_at_last_day
            results.append({
                "day": completed_day,
                "earned": daily_earned,
                "reputation": sim.reputation,
                "score": sim.earned + tuning["score"]["reputation_multiplier"] * math.floor(sim.reputation),
            })
            earned_at_last_day = sim.earned

    if not sim.done and crashes == 0:
        crashes += 1
        diagnostics.append({"day": sim.day, "error": "DaySim did not finish before the derived tick bound"})

    result = {
        "days": days,
        "days_completed": sim.days_completed,
        "crashes": crashes,
        "results": results,
        "duration_s": time.perf_counter() - started,
    }
    if diagnostics:
        result["diagnostics"] = diagnostics
    try:
        with open(out_path, "w", encoding="utf-8", newline="\n") as output:
            json.dump(result, output, ensure_ascii=False, indent=2)
            output.write("\n")
    except OSError as exc:
        print(f"lỗi ghi soak: {exc}", file=sys.stderr)
        return 1, result
    return (0 if sim.done and sim.days_completed == days and crashes == 0 else 1), result


def main(argv=None):
    parser = argparse.ArgumentParser(prog="chonoi.soak")
    parser.add_argument("--seed", required=True, type=_integer("--seed"))
    parser.add_argument("--days", required=True, type=_integer("--days", 1))
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        code, result = run_soak(args.seed, args.days, args.out)
    except (BadInput, KeyError, TypeError, ValueError) as exc:
        print(f"đầu vào hoặc tuning không hợp lệ: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
