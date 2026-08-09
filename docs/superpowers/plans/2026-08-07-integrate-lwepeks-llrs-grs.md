# LWE-PEKS, LLRS, and GRS Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Integrate the latest LWE-PEKS, LLRS, and GRS implementations into Cryptographic-Schemes as independently executable, documented scheme directories.

**Architecture:** Preserve one canonical implementation in each upstream language family without importing nested Git history, binary archives, bundled JARs, or generated figures. LWE-PEKS and LLRS become single-file Python experiment drivers using the repository Parser/Saver contract; GRS becomes a single-file Java source using the repository's JPBC and POI dependencies. Existing Python and Java matrix workflows invoke the new entry points.

**Tech Stack:** Python 3.12+, NumPy, Java 11+, JPBC 2.0.0, Apache POI, GitHub Actions.

---

### Task 1: Establish source provenance and target structure

**Files:**
- Create: `docs/superpowers/plans/2026-08-07-integrate-lwepeks-llrs-grs.md`

- [x] Record the imported upstream revisions in the pull-request description:
  - LWE-PEKS: `fc6202f46fbd0e48567c514d0b18d29d40d513d5`
  - LLRS: `1f1d46c46a17aad843fa30352546e37b8fe9906a`
  - GRS: `c0ec5024cb8321884fb254a4ddeabe1657f40b79`
- [x] Exclude upstream `.git` data, ZIP archives, generated PNG figures, and bundled JAR files.
- [x] Verify the worktree starts clean with `git status --short` and that the branch is `codex/integrate-lwepeks-llrs-grs`.

### Task 2: Add the LWE-PEKS Python experiment

**Files:**
- Create: `SchemeLWEPEKS/SchemeLWEPEKS.py`
- Create: `SchemeLWEPEKS/requirements.txt`
- Create: `SchemeLWEPEKS/README.md`

- [x] Add a test invocation before implementation and verify that it fails because the entry point is absent:

```shell
python SchemeLWEPEKS/SchemeLWEPEKS.py -o /tmp/SchemeLWEPEKS.json -r 1 -t 0 -y
```

- [x] Implement the common `Parser` and `Saver` contract used by `SchemeLBPEAKS.py`, including script-relative output paths, protected extensions, quiet mode, run count, waiting time, and overwrite confirmation.
- [x] Port the upstream simulation into `SchemeLWEPEKS` with `Setup`, `Derive`, `Encrypt`, `Trapdoor`, and `Search` procedures. Use bounded experiment dimensions suitable for CI while retaining the two upstream parameter families as metadata.
- [x] Make `conductScheme` return setup, derive, encrypt, trapdoor, and search timings; matrix-derived storage measurements; system validity; and matched-keyword correctness.
- [x] Run the entry point with JSON and XLSX output and expect exit code `0`, a saved result, and `Is the scheme correct? Yes.` in verbose output.

### Task 3: Add the LLRS Python experiment

**Files:**
- Create: `SchemeLLRS/SchemeLLRS.py`
- Create: `SchemeLLRS/requirements.txt`
- Create: `SchemeLLRS/README.md`

- [x] Add a test invocation before implementation and verify that it fails because the entry point is absent:

```shell
python SchemeLLRS/SchemeLLRS.py -o /tmp/SchemeLLRS.json -r 1 -t 0 -y
```

- [x] Consolidate the procedure flow represented by upstream `LLRS_v4.0.py` into one bounded modular simulation suitable for repeatable automated experiments.
- [x] Replace the legacy command-line loop with the common `Parser` and `Saver` contract while preserving Setup, KeyExtract, KeyUpdate, Sign, Verify, and Link as distinct measured procedures.
- [x] Use small valid defaults (modulus `251`, dimension `4`, and ring sizes `2` and `4`) for CI; expose the upstream production defaults in the README rather than allocating multi-gigabyte matrices in CI.
- [x] Run the entry point with JSON and XLSX output and expect exit code `0`, successful verification, and linkability for two signatures from the same signer.

### Task 4: Add the GRS Java experiment

**Files:**
- Create: `SchemeGRS/SchemeGRS.java`
- Create: `SchemeGRS/README.md`

- [x] Add a compilation test before implementation and verify that it fails because the source is absent:

```shell
javac -Xlint:all -cp 'lib/*' -d /tmp/scheme-grs-build SchemeGRS/SchemeGRS.java
```

- [x] Consolidate upstream `PARS`, `Setup`, `KeyGen`, `SignI`, `VerifyI`, `SignII`, `VerifyII`, and `Start` into one source file.
- [x] Replace ClassMexer with encoded-element byte lengths so only the repository JPBC and POI dependency set is required.
- [x] Reuse the Java `Parser` and `Saver` contract from `SchemeLBPEAKS.java`, retain script-relative paths, and sort standard-library imports before external imports.
- [x] Generate only nonzero ZR values where inversion is required, hash length-delimited element bytes with SHA3-256, and verify both GRS signature constructions.
- [x] Compile with `-Xlint:all`, execute one run for ring sizes `2`, `4`, and `8`, and expect exit code `0` and both verification results to be `Yes`.

### Task 5: Connect documentation and CI

**Files:**
- Modify: `README.md`
- Modify: `.github/workflows/runPython.yml`
- Modify: `.github/workflows/runJava.yml`

- [x] Add alphabetically placed root entries for `SchemeGRS`, `SchemeLLRS`, and `SchemeLWEPEKS` with links to their canonical entry points.
- [x] Add `executeSchemeLWEPEKS` and `executeSchemeLLRS` workflow-dispatch inputs and append both Python files to the Python matrix.
- [x] Add `executeSchemeGRS` workflow-dispatch input and append `SchemeGRS/SchemeGRS.java` to the Java matrix.
- [x] Include each scheme's `requirements.txt` in Python dependency resolution through the workflow's existing per-directory mechanism.
- [x] Validate YAML parsing and matrix preparation without changing unrelated default selections.

### Task 6: Verify and publish

**Files:**
- Verify all files listed in Tasks 1–5.

- [x] Run `python -m py_compile SchemeLWEPEKS/SchemeLWEPEKS.py SchemeLLRS/SchemeLLRS.py` and expect exit code `0`.
- [x] Run both Python schemes with `-r 1 -t 0 -y` and JSON output; expect exit code `0` and nonempty result files.
- [x] Compile and run `SchemeGRS.java` using `lib/*`; expect exit code `0` and a nonempty result file.
- [x] Run `git diff --check`; expect no whitespace errors.
- [x] Confirm Python files contain no explicit line continuations and Java source has no extra final newline.
- [x] Commit with an English message, push `codex/integrate-lwepeks-llrs-grs` to the fork, and create one ready pull request against `yueryang/Cryptographic-Schemes:main`.
