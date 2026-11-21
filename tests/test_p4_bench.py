"""Unit tests cho module Benchmark Phase 4 (chonoi/bench.py) — AC-P4-02."""

import json
import math
import os
import tempfile
import unittest

from chonoi.bench import compute_bench_metrics, run_benchmark


class BenchPhase4Tests(unittest.TestCase):
    def test_compute_metrics_uniform_60fps(self):
        """1800 khung đều ở 60 FPS (1/60 s): avg_fps = 60, p1_low_fps = 60."""
        dt = 1.0 / 60.0
        frames = [dt] * 1800
        metrics = compute_bench_metrics(frames, load_ms=120.5)

        self.assertEqual(metrics["frames"], 1800)
        self.assertAlmostEqual(metrics["measured_s"], 30.0, places=2)
        self.assertAlmostEqual(metrics["avg_fps"], 60.0, places=2)
        self.assertAlmostEqual(metrics["p1_low_fps"], 60.0, places=2)
        self.assertEqual(metrics["load_ms"], 120.5)

    def test_compute_metrics_stutter_drops_p1_low(self):
        """100 khung với 99 khung 60 FPS và 1 khung bị khựng 100ms (10 FPS) -> p1_low tụt xuống 10."""
        dt = 1.0 / 60.0
        frames = [dt] * 99 + [0.1]  # 1 khung 100 ms
        metrics = compute_bench_metrics(frames, load_ms=50.0)

        self.assertEqual(metrics["frames"], 100)
        # 1% của 100 là 1 khung chậm nhất (chính là khung 0.1s)
        # p1_low_fps = 1.0 / 0.1 = 10.0
        self.assertAlmostEqual(metrics["p1_low_fps"], 10.0, places=2)
        # avg_fps vẫn ở mức ~57 FPS
        self.assertGreater(metrics["avg_fps"], 50.0)

    def test_compute_metrics_empty_list_and_single_frame(self):
        """Dãy rỗng hoặc 1 khung không gây lỗi chia cho 0."""
        empty_metrics = compute_bench_metrics([], load_ms=10.0)
        self.assertEqual(empty_metrics["frames"], 0)
        self.assertEqual(empty_metrics["avg_fps"], 0.0)
        self.assertEqual(empty_metrics["p1_low_fps"], 0.0)

        single_metrics = compute_bench_metrics([0.02], load_ms=15.0)
        self.assertEqual(single_metrics["frames"], 1)
        self.assertAlmostEqual(single_metrics["avg_fps"], 50.0, places=2)
        self.assertAlmostEqual(single_metrics["p1_low_fps"], 50.0, places=2)

    def test_bench_output_json_format_and_keys(self):
        """Kết quả ghi ra file JSON phải đủ 5 trường với đúng kiểu dữ liệu."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = os.path.join(tmpdir, "test_bench.json")
            # Chạy benchmark mô phỏng nhanh 0.1s không mở browser
            metrics = run_benchmark(seed=42, duration=0.1, warmup=0.0, out_path=out_file, no_browser=True)

            self.assertTrue(os.path.exists(out_file))
            with open(out_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            expected_keys = {"avg_fps", "p1_low_fps", "load_ms", "measured_s", "frames"}
            self.assertEqual(set(data.keys()), expected_keys)
            self.assertIsInstance(data["avg_fps"], (int, float))
            self.assertIsInstance(data["p1_low_fps"], (int, float))
            self.assertIsInstance(data["load_ms"], (int, float))
            self.assertIsInstance(data["measured_s"], (int, float))
            self.assertIsInstance(data["frames"], int)


if __name__ == "__main__":
    unittest.main()
