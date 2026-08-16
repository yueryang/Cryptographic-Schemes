# Coefficient Computation Runtime Output Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Print each completed coefficient-comparison result immediately in non-quiet mode while preserving quiet mode and all computation results.

**Architecture:** Add one private formatter for a result row and one private recorder that appends the unchanged row before conditionally printing it. Route all basic and device result creation through the recorder and remove the final bulk table print.

**Tech Stack:** Python 3 standard library, `unittest`, fake Charm-Crypto modules for deterministic tests.

---

### Task 1: Runtime output regression tests

**Files:**
- Create: `testSchemeCoefficientComputation.py`

- [x] Write a test that interrupts the device phase and asserts that completed basic results were already printed as labeled blocks.
- [x] Write a quiet-mode test that asserts no per-result output is produced.
- [x] Run `python3 -m unittest -v testSchemeCoefficientComputation.py` and verify the verbose test fails because output is currently delayed until the end.

### Task 2: Incremental result reporting

**Files:**
- Modify: `SchemeCoefficientComputation/SchemeCoefficientComputation.py`

- [x] Replace the bulk table printer with a single-result block formatter.
- [x] Add a recorder that appends each unchanged result and prints it only when `isVerbose is not False`.
- [x] Route all five basic/device append sites through the recorder.
- [x] Remove the final bulk print from `conductScheme`.
- [x] Re-run the focused tests and verify both pass.

### Task 3: Complete verification

**Files:**
- Verify: `SchemeCoefficientComputation/SchemeCoefficientComputation.py`
- Verify: `testSchemeCoefficientComputation.py`

- [x] Run static compilation.
- [x] Run the focused unit tests.
- [x] Run verbose and quiet command-line smoke tests with fake Charm-Crypto and confirm the output contract.
- [x] Inspect the diff to confirm calculation and saved-result rows are unchanged.
