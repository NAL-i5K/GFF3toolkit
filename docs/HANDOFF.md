# Handoff Notes

## Snapshot
- Date: 2026-05-15
- Branch: chore/version-updates-followup
- Latest commit before this note: 6862a83
- Goal completed locally: Python 3.14 compatibility reassessment with runtime and packaging checks.
- Note: several follow-up review items remained open after this validation.

## What Was Validated Under Python 3.14
Environment used:
- Local venv: .venv-assess
- Python: 3.14.4

Commands run:
1. Unit tests with warnings enabled
   - /Users/cchilders/git-repos/GFF3toolkit/.venv-assess/bin/python -W default -m unittest discover -s tests/unit -p 'test_*.py'
   - Result: PASS (82 tests)
2. Unit tests with DeprecationWarning treated as errors
   - /Users/cchilders/git-repos/GFF3toolkit/.venv-assess/bin/python -W error::DeprecationWarning -m unittest discover -s tests/unit -p 'test_*.py'
   - Result: PASS (82 tests)
3. CLI smoke tests
   - /Users/cchilders/git-repos/GFF3toolkit/.venv-assess/bin/python -W default tests.py
   - Result: PASS after bundled BLAST binaries were present.
4. Packaging build
   - /Users/cchilders/git-repos/GFF3toolkit/.venv-assess/bin/python -W default -m build
   - Result: PASS (sdist and wheel built successfully)

## Findings
### 1) Python 3.14 runtime compatibility
- No active Python 3.14 language/runtime breakage found in project code during unit tests.
- Unit tests pass even when DeprecationWarning is promoted to an error.

### 2) Packaging deprecations still present
- Setuptools deprecation warnings are emitted during build for license metadata.
- Sources:
  - pyproject.toml uses license table form: license = { text = "Public Domain" }
  - pyproject.toml includes classifier: "License :: Public Domain"
- Warning indicates migration should be completed before 2027-02-18.

### 3) setup.py uses private setuptools fallback path
- setup.py imports setuptools._distutils.command.build in fallback path.
- This works now, but it is a private path and has upgrade fragility risk.
- The BLAST bundle step also needs to be idempotent and safe against archive path traversal.

### 4) Smoke test caveat
- tests.py requires bundled BLAST executables to be available.
- When BLAST binaries are missing, tests.py fails before compatibility conclusions can be made.
- Once BLAST artifacts are present, tests.py passes on Python 3.14.

## CI Coverage for Python 3.14
- .github/workflows/build.yml includes:
  - build5-Docs-build on Python 3.14
  - build6-Python-314-runtime on Python 3.14 (smoke + unit tests)

## Recommended Follow-Up
1. Update pyproject.toml license metadata to remove setuptools-deprecated forms.
2. Consider removing private setuptools._distutils fallback usage in setup.py.
3. Keep tests.py BLAST preflight behavior, but ensure local instructions clearly explain BLAST artifact requirements.
4. Resolve the remaining review comments in the workflow, docs, setup, and tests before treating the branch as finished.

## Fast Resume Checklist
1. Confirm branch: chore/version-updates-followup
2. Re-run:
   - .venv-assess/bin/python -W error::DeprecationWarning -m unittest discover -s tests/unit -p 'test_*.py'
   - .venv-assess/bin/python -W default tests.py
   - .venv-assess/bin/python -W default -m build
3. Address pyproject.toml license deprecation warnings.
