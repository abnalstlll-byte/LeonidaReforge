#!/usr/bin/env python3
"""Synthetic test inventory and subsystem map (DX-10).

Discovers and classifies test files across runtime, shader, tools, and viewer
subsystems, tagging execution prerequisites and synthetic coverage gaps.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

SUBSYSTEMS = ("runtime", "shader", "tools", "viewer")


def classify_subsystem(rel_path: str, content: str) -> str:
    """Classify a test into its primary subsystem."""
    path_lower = rel_path.lower()

    if path_lower.startswith("runtime/test") or "gta6rt" in path_lower:
        return "runtime"
    if "semantic" in path_lower or "spirv" in path_lower or "rdna2" in path_lower:
        return "shader"
    if "viewer" in path_lower:
        return "viewer"

    # Inspect content keywords
    if any(k in content for k in ("rdna2spirv", "OpCapability", "v_add", "s_endpgm")):
        return "shader"
    if any(k in content for k in ("ID3D12Device", "VulkanContext", "pe_loader", "xma2")):
        return "runtime"
    if any(k in content for k in ("viewer", "lod", "streaming_server")):
        return "viewer"

    return "tools"


def classify_runner(path: Path, content: str) -> str:
    """Determine the test runner required."""
    suffix = path.suffix.lower()
    if suffix in (".cpp", ".c", ".h"):
        return "ctest_cpp"
    if suffix in (".cjs", ".js", ".mjs"):
        return "node_test"
    if suffix == ".py":
        if "import pytest" in content or "pytest.mark" in content:
            return "pytest"
        if "unittest" in content or "__main__" in content:
            return "python_unittest"
        return "pytest"
    return "unknown"


def detect_prerequisites(runner: str, content: str) -> list[str]:
    """Detect prerequisites required to execute the test."""
    prereqs = []
    if runner == "ctest_cpp":
        prereqs.extend(["cmake", "compiler"])
        if "vulkan" in content.lower():
            prereqs.append("vulkan_sdk")
    elif runner == "node_test":
        prereqs.append("node")
    elif runner == "pytest":
        prereqs.append("pytest")
    elif runner == "python_unittest":
        prereqs.append("stdlib")

    if "llvm-mc" in content.lower() or "llvm_mc" in content.lower():
        prereqs.append("llvm_mc")
    if "spirv-as" in content or "spirv-val" in content:
        prereqs.append("spirv_tools")

    return sorted(set(prereqs))


def scan_tests(root: Path) -> list[dict]:
    """Scan and catalog all test files in the repository."""
    inventory = []
    search_dirs = [
        root / "tests",
        root / "runtime" / "test",
    ]

    for search_dir in search_dirs:
        if not search_dir.is_dir():
            continue
        for p in search_dir.rglob("*"):
            if not p.is_file():
                continue
            name_lower = p.name.lower()
            if not (
                name_lower.startswith("test_")
                or name_lower.endswith("_test.py")
                or name_lower.endswith("_test.cpp")
                or name_lower.endswith("_test.cjs")
            ):
                continue

            rel_path = p.relative_to(root).as_posix()
            try:
                content = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                content = ""

            subsystem = classify_subsystem(rel_path, content)
            runner = classify_runner(p, content)
            prereqs = detect_prerequisites(runner, content)

            needs_retail = any(
                marker in content
                for marker in ("LEONIDA_GAME_DIR", "LEONIDA_MOVIE", "requires_retail_package")
            )

            inventory.append({
                "path": rel_path,
                "name": p.name,
                "subsystem": subsystem,
                "runner": runner,
                "prerequisites": prereqs,
                "is_synthetic": not needs_retail,
                "needs_retail_game_data": needs_retail,
            })

    return sorted(inventory, key=lambda x: x["path"])


def build_summary(inventory: list[dict]) -> dict:
    """Aggregate inventory into subsystem and runner metrics."""
    by_subsystem = {s: {"total": 0, "synthetic": 0, "retail_gated": 0} for s in SUBSYSTEMS}
    by_runner = {}

    for item in inventory:
        sub = item["subsystem"]
        if sub in by_subsystem:
            by_subsystem[sub]["total"] += 1
            if item["is_synthetic"]:
                by_subsystem[sub]["synthetic"] += 1
            else:
                by_subsystem[sub]["retail_gated"] += 1

        runner = item["runner"]
        by_runner[runner] = by_runner.get(runner, 0) + 1

    total_tests = len(inventory)
    total_synthetic = sum(1 for x in inventory if x["is_synthetic"])

    return {
        "schema_version": 1,
        "total_test_files": total_tests,
        "total_synthetic_files": total_synthetic,
        "synthetic_coverage_pct": round((total_synthetic / total_tests * 100) if total_tests else 0, 1),
        "by_subsystem": by_subsystem,
        "by_runner": by_runner,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="test_inventory.py",
        description="Synthetic test inventory and subsystem map (DX-10).",
    )
    parser.add_argument("--json", action="store_true", help="output machine-readable JSON inventory")
    parser.add_argument("--summary", action="store_true", help="output formatted subsystem summary table")
    parser.add_argument(
        "--subsystem",
        choices=SUBSYSTEMS,
        help="filter tests by subsystem",
    )
    parser.add_argument("--gaps", action="store_true", help="show tests with retail prerequisites or gaps")
    args = parser.parse_args(argv)

    inventory = scan_tests(ROOT)
    summary = build_summary(inventory)

    if args.subsystem:
        inventory = [x for x in inventory if x["subsystem"] == args.subsystem]

    if args.gaps:
        inventory = [x for x in inventory if x["needs_retail_game_data"]]

    if args.json:
        result = {
            **summary,
            "tests": inventory,
        }
        print(json.dumps(result, indent=2))
        return 0

    # Human-readable output
    print("=" * 72)
    print("Leonida Synthetic Test Inventory & Subsystem Map (DX-10)")
    print("=" * 72)
    print(f"Total Test Files: {summary['total_test_files']}")
    print(f"Synthetic Tests:  {summary['total_synthetic_files']} ({summary['synthetic_coverage_pct']}%)")
    print("\nSubsystem Breakdown:")
    print(f"  {'Subsystem':<12} {'Total':<8} {'Synthetic':<12} {'Retail Gated':<12}")
    print("  " + "-" * 44)
    for sub, stats in summary["by_subsystem"].items():
        print(f"  {sub:<12} {stats['total']:<8} {stats['synthetic']:<12} {stats['retail_gated']:<12}")

    print("\nRunner Distribution:")
    for runner, count in sorted(summary["by_runner"].items()):
        print(f"  - {runner:<18}: {count}")

    if args.subsystem or args.gaps:
        print("\nFiltered Tests:")
        for item in inventory:
            prereq_str = ", ".join(item["prerequisites"]) if item["prerequisites"] else "none"
            print(f"  [{item['subsystem']}] {item['path']} ({item['runner']}) — prereqs: {prereq_str}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
