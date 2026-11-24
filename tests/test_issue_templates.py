"""Validate GitHub issue template structure, required fields, and clean-room constraints (DX-09)."""
from __future__ import annotations

import os
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
BUG_REPORT_TEMPLATE = ROOT / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml"
CONFIG_TEMPLATE = ROOT / ".github" / "ISSUE_TEMPLATE" / "config.yml"


class IssueTemplateTests(unittest.TestCase):
    def test_bug_report_template_exists(self):
        self.assertTrue(BUG_REPORT_TEMPLATE.is_file(), f"{BUG_REPORT_TEMPLATE} is missing")

    def test_bug_report_required_fields_and_ids(self):
        text = BUG_REPORT_TEMPLATE.read_text(encoding="utf-8")

        # Basic metadata
        self.assertIn("name: Bug report", text)
        self.assertIn("labels: [bug]", text)

        # Required field IDs per DX-09 specification
        required_ids = [
            "summary",
            "commit",
            "environment",
            "subsystem",
            "command_steps",
            "expected",
            "actual",
            "synthetic_repro",
            "provenance",
            "clean_room_checklist",
        ]
        for field_id in required_ids:
            with self.subTest(id=field_id):
                pattern = rf"id:\s+{re.escape(field_id)}\b"
                self.assertTrue(
                    re.search(pattern, text),
                    f"Template missing required field id '{field_id}'",
                )

    def test_bug_report_clean_room_directives(self):
        text = BUG_REPORT_TEMPLATE.read_text(encoding="utf-8")

        # Must explicitly warn against retail game data in header and checklist
        self.assertIn("Never attach retail game executables", text)
        self.assertIn("synthetic fixtures", text.lower())
        self.assertIn("NO retail game files", text)
        self.assertIn("scripts/check_no_game_data.py", text)

    def test_bug_report_provenance_separation(self):
        text = BUG_REPORT_TEMPLATE.read_text(encoding="utf-8")

        # Must distinguish current measurements from historical claims
        self.assertIn("Evidence Provenance", text)
        self.assertIn("current measurements", text)
        self.assertIn("Historical claims", text)

    def test_template_uses_lf_line_endings(self):
        raw_bytes = BUG_REPORT_TEMPLATE.read_bytes()
        self.assertNotIn(b"\r\n", raw_bytes, "Template must use Unix LF line endings")


if __name__ == "__main__":
    unittest.main()
