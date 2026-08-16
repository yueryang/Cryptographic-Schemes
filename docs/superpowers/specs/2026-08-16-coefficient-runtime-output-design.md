# Coefficient Computation Runtime Output Design

## Goal

Make `SchemeCoefficientComputation.py` report completed comparison results while a non-quiet execution is still running, using the block-oriented console style of the other scheme programs.

## Behavior

Each completed seven-field result is printed immediately with the target, curve, multiplicative-identity reliability, solution, run count, correctness count, and average time on separate lines, followed by a blank line. The existing result row, timing, correctness, saving, and exit-status contracts remain unchanged.

The `-q`, `/q`, and equivalent quiet options continue to suppress all per-result output. Diagnostics for actual failures retain their existing behavior. The final tab-separated table is removed to avoid duplicate output after incremental reporting.

## Verification

A focused unit test uses a fake Charm-Crypto environment. It proves that output is already present if device comparison is interrupted after the basic phase, verifies the block labels, and verifies that quiet mode produces no output. Static compilation and a command-line smoke test cover the complete file.
