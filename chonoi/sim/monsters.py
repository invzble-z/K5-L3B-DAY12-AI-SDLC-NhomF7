"""Cá Sấu tuần tra, truy đuổi và lùi sau khi chạm người chơi."""

import math

from ..ids import sort_by_id


class MonsterSystem:
    def __init__(self, tuning, spawns, bounds, tick_hz):
        self.tuning = tuning
        self.bounds = bounds
        self.tick_hz = tick_hz
        self.monsters = []
        for spawn in spawns:
            waypoints = [[float(c) for c in point] for point in spawn["waypoints"]]
            pos = spawn.get("pos", waypoints[0])
            self.monsters.append({
                "id": spawn["id"],
                "species": spawn["species"],
                "pos": [float(c) for c in pos],
                "waypoints": waypoints,
                "waypoint_index": 1,
                "state": "patrol",
                "recoil_ticks": 0,
                "recoil_dir": [0.0, 0.0],
            })

    def snapshot(self):
        return [
            {"id": monster["id"], "species": monster["species"], "pos": monster["pos"],
             "state": monster["state"], "waypoint_index": monster["waypoint_index"],
             "recoil_ticks": monster["recoil_ticks"]}
            for monster in sort_by_id(self.monsters)
        ]

    def step(self, player_pos, allow_hit):
        eligible = set()
        for monster in sort_by_id(self.monsters):
            species = self.tuning["species"][monster["species"]]
            if monster["state"] == "recoil":
                self._recoil(monster, species)
                continue

            distance = math.dist(monster["pos"], player_pos)
            if monster["state"] == "chase":
                if player_pos[1] < species["depths"][0] or distance > species["exit_radius"]:
                    monster["state"] = "patrol"
                    continue
                self._move_toward(monster, player_pos, species["chase_speed"], species["depths"])
            elif (player_pos[1] >= species["depths"][0]
                  and distance <= species["detect_radius"]):
                monster["state"] = "chase"
                self._move_toward(monster, player_pos, species["chase_speed"], species["depths"])
            else:
                target = monster["waypoints"][monster["waypoint_index"]]
                arrived = self._move_toward(
                    monster, target, species["patrol_speed"], species["depths"]
                )
                if arrived:
                    monster["waypoint_index"] = (
                        0 if monster["waypoint_index"] == 1 else 1
                    )
            eligible.add(monster["id"])

        if not allow_hit:
            return None
        nearest = None
        nearest_distance = math.inf
        for monster in sort_by_id(self.monsters):
            if monster["id"] not in eligible:
                continue
            species = self.tuning["species"][monster["species"]]
            if player_pos[1] < species["depths"][0]:
                continue
            distance = math.dist(monster["pos"], player_pos)
            if distance <= species["hit_radius"] and distance < nearest_distance:
                nearest = monster
                nearest_distance = distance
        return nearest

    def start_recoil(self, monster, player_pos):
        dx = monster["pos"][0] - player_pos[0]
        dy = monster["pos"][1] - player_pos[1]
        distance = math.hypot(dx, dy)
        monster["recoil_dir"] = [1.0, 0.0] if distance == 0 else [dx / distance, dy / distance]
        monster["state"] = "recoil"
        monster["recoil_ticks"] = self.tuning["species"][monster["species"]]["recoil_ticks"]

    def _recoil(self, monster, species):
        distance = self.tuning["species"][monster["species"]]["recoil_dist"]
        direction = monster["recoil_dir"]
        self._place(monster, [
            monster["pos"][0] + direction[0] * distance,
            monster["pos"][1] + direction[1] * distance,
        ], species["depths"])
        monster["recoil_ticks"] -= 1
        if monster["recoil_ticks"] == 0:
            monster["state"] = "patrol"

    def _move_toward(self, monster, target, speed, depths):
        dx = target[0] - monster["pos"][0]
        dy = target[1] - monster["pos"][1]
        distance = math.hypot(dx, dy)
        step_distance = speed / self.tick_hz
        if distance <= step_distance or math.isclose(distance, step_distance):
            self._place(monster, target, depths)
            return True
        if distance > 0:
            self._place(monster, [
                monster["pos"][0] + dx * step_distance / distance,
                monster["pos"][1] + dy * step_distance / distance,
            ], depths)
        return False

    def _place(self, monster, pos, depths):
        x_bounds = self.bounds["x"]
        depth_min = max(self.bounds["d"][0], depths[0])
        depth_max = min(self.bounds["d"][1], depths[1])
        monster["pos"] = [
            min(x_bounds[1], max(x_bounds[0], pos[0])),
            min(depth_max, max(depth_min, pos[1])),
        ]
