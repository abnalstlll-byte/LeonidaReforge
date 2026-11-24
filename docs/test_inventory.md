# Synthetic Test Inventory & Subsystem Map (DX-10)

This document provides the authoritative subsystem test map and prerequisite catalog for Leonida, implemented under roadmap task **DX-10**.

## Overview

The repository contains **1,177** test files, of which **1,168 (99.2%)** are fully synthetic and can be run without retail game packages, executables, or proprietary assets.

```bash
# Generate the full subsystem breakdown and metrics
python -I tools/test_inventory.py --summary

# Output machine-readable JSON inventory
python -I tools/test_inventory.py --json

# Filter tests by subsystem (runtime, shader, tools, viewer)
python -I tools/test_inventory.py --subsystem shader

# Display tests requiring retail package prerequisites
python -I tools/test_inventory.py --gaps
```

## Subsystem Breakdown

| Subsystem | Total Files | Synthetic | Retail Gated | Primary Runners | Key Coverage Areas |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Shader** | 600 | 600 (100%) | 0 | `python_unittest` | RDNA2 -> SPIR-V translator, float ALU rounding, vector compares, atomics, mesh/wave64 dispatch. |
| **Tools** | 315 | 314 (99.7%) | 1 | `python_unittest`, `pytest` | Asset exporters, PE inspection, manifest checkers, BCPack/texture swizzlers, developer scripts. |
| **Runtime** | 228 | 220 (96.5%) | 8 | `ctest_cpp` | D3D12/Vulkan shims, PE loader, root signature parser, XMA2 audio shims, memory and descriptor heaps. |
| **Viewer** | 34 | 34 (100%) | 0 | `python_unittest`, `node_test` | Map viewer HTTP streaming, LOD residency handoffs, camera positioning, world grid chunking. |

## Runner Distribution

- **`python_unittest` (918 files)**: Pure standard-library Python test suites runnable with `python -I`.
- **`ctest_cpp` (226 files)**: Native C++20 tests built with CMake/Ninja under `runtime/build/`.
- **`pytest` (31 files)**: Tests requiring the virtual environment dependencies pinned in `tests/requirements.txt`.
- **`node_test` (2 files)**: Viewer streaming protocol tests running under Node.js (`node --test`).

## Retail-Gated Tests (Gaps)

Only 9 tests require the retail package (`LEONIDA_GAME_DIR` / `LEONIDA_MOVIE`), located primarily in `runtime/test/` for end-to-end boot and loader verification against the retail package manifest. All other 1,168 tests execute strictly against hand-authored synthetic fixtures.
