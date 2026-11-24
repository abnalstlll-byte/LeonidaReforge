"""Unit tests for the synthetic test inventory tool (DX-10)."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_TOOL = ROOT / "tools" / "test_inventory.py"


class TestInventoryTests(unittest.TestCase):
    def invoke(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-I", "-B", str(INVENTORY_TOOL), *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_help_exits_cleanly(self):
        proc = self.invoke("--help")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("DX-10", proc.stdout)
        self.assertIn("--summary", proc.stdout)
        self.assertIn("--json", proc.stdout)
        self.assertIn("--subsystem", proc.stdout)

    def test_summary_output(self):
        proc = self.invoke("--summary")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Subsystem Map (DX-10)", proc.stdout)
        self.assertIn("runtime", proc.stdout)
        self.assertIn("shader", proc.stdout)
        self.assertIn("tools", proc.stdout)
        self.assertIn("viewer", proc.stdout)

    def test_json_schema_validation(self):
        proc = self.invoke("--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(data["schema_version"], 1)
        self.assertGreater(data["total_test_files"], 1000)
        self.assertGreater(data["synthetic_coverage_pct"], 90.0)
        self.assertIn("by_subsystem", data)
        self.assertIn("runtime", data["by_subsystem"])
        self.assertIn("shader", data["by_subsystem"])
        self.assertIn("tests", data)
        self.assertIsInstance(data["tests"], list)

    def test_subsystem_filter(self):
        proc = self.invoke("--subsystem", "shader", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        for t in data["tests"]:
            self.assertEqual(t["subsystem"], "shader")

    def test_gaps_filter(self):
        proc = self.invoke("--gaps", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        for t in data["tests"]:
            self.assertTrue(t["needs_retail_game_data"])


if __name__ == "__main__":
    unittest.main()
