# Handoff Log (Internal)

This file is for internal project handoff notes and work-in-progress context.
Each new entry should include an explicit date and time stamp.

## 2026-05-15 17:21 UTC - Python 3.14 compatibility reassessment

### Snapshot
- Branch: chore/version-updates-followup
- Latest commit before this note: 6862a83
- Goal completed locally: Python 3.14 compatibility reassessment with runtime and packaging checks.
- Note: several follow-up review items remained open after this validation.

### What Was Validated Under Python 3.14
- Environment:
  - Local venv: .venv-assess
  - Python: 3.14.4
- Commands run:
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

### Findings
1. Python 3.14 runtime compatibility
   - No active Python 3.14 language/runtime breakage found in project code during unit tests.
   - Unit tests pass even when DeprecationWarning is promoted to an error.
2. Packaging deprecations still present
   - Setuptools deprecation warnings are emitted during build for license metadata.
   - Sources:
     - pyproject.toml uses license table form: license = { text = "Public Domain" }
     - pyproject.toml includes classifier: "License :: Public Domain"
   - Warning indicates migration should be completed before 2027-02-18.
3. setup.py uses private setuptools fallback path
   - setup.py imports setuptools._distutils.command.build in fallback path.
   - This works now, but it is a private path and has upgrade fragility risk.
   - The BLAST bundle step also needs to be idempotent and safe against archive path traversal.
4. Smoke test caveat
   - tests.py requires bundled BLAST executables to be available.
   - When BLAST binaries are missing, tests.py fails before compatibility conclusions can be made.
   - Once BLAST artifacts are present, tests.py passes on Python 3.14.

### CI Coverage for Python 3.14
- .github/workflows/build.yml includes:
  - build5-Docs-build on Python 3.14
  - build6-Python-314-runtime on Python 3.14 (smoke + unit tests)

### Recommended Follow-Up
1. Update pyproject.toml license metadata to remove setuptools-deprecated forms.
2. Consider removing private setuptools._distutils fallback usage in setup.py.
3. Keep tests.py BLAST preflight behavior, but ensure local instructions clearly explain BLAST artifact requirements.
4. Resolve the remaining review comments in the workflow, docs, setup, and tests before treating the branch as finished.

### Fast Resume Checklist
1. Confirm branch: chore/version-updates-followup
2. Re-run:
   - .venv-assess/bin/python -W error::DeprecationWarning -m unittest discover -s tests/unit -p 'test_*.py'
   - .venv-assess/bin/python -W default tests.py
   - .venv-assess/bin/python -W default -m build
3. Address pyproject.toml license deprecation warnings.

## 2026-05-18 19:05 UTC - Post-merge stabilization on master (badges, CI, Codecov, RTD)

### Snapshot
- Branch: master
- HEAD commit: e624cad
- Goal: stabilize post-PR-145 status indicators (GitHub badge, Codecov badge/ingestion, RTD integration) and remove CI warnings blocking confidence.

### What Was Completed Today
1. PR #145 merged and verified on master
   - Merge commit: 8465de5
2. README badge targeting adjusted to explicit master endpoints
   - Commit: f4c5fb2
3. Coverage upload path moved from legacy codecov CLI to Codecov GitHub Action
   - Initial migration: 46ce9d9
4. CI failure in coverage job fixed after migration
   - Symptom: "Codecov: Failed to properly create commit" in build1
   - Mitigation: made Codecov upload non-blocking and kept coverage summary gate
   - Commit: e038beb
5. Node 20 deprecation annotation removed from Codecov path
   - Upgrade: codecov/codecov-action v5 -> v6 (node24 support)
   - Commit: e624cad

### Current Status
1. GitHub Actions workflow
   - Latest run after e038beb was green with only warning/notice annotations.
   - Node20 warning source identified as dependency path behind Codecov action; workflow now uses v6 to resolve this.
2. Codecov branch page
   - Previously stale at commit c83f854 with 16.19% coverage.
   - Root issue appears to be ingestion lag/upload acceptance, not test execution failure on master.
3. Read the Docs integration
   - RTD incoming webhook rejects deliveries without secret (HTTP 400).
   - Requires RTD/GitHub webhook secret configuration update outside repo code.

### Why Coverage Looked "Too Low"
- The 16.19% figure reflected stale Codecov branch context and/or runs where full CLI smoke path contribution was not reflected in uploaded data.
- Local unit-only run reproduces low percentage profile; full workflow runs exercise more paths, but Codecov must ingest latest commit for badge/report to update.

### Open Items (High Priority Tomorrow)
1. Confirm latest Codecov ingestion for master
   - Verify Codecov "Source: latest commit" advances beyond c83f854 to e624cad (or newer).
2. If still stale, configure authenticated upload
   - Add repository/org CODECOV_TOKEN secret and optionally set fail_ci_if_error back to true after confirmation.
3. Fix RTD webhook secret
   - Recreate or update GitHub webhook from RTD integration page with secret configured.
4. Verify badges after backend refresh
   - GitHub build badge, Codecov badge, RTD badge all reflect current state.

### Fast Resume Checklist (Tomorrow)
1. Check latest CI run status for commit e624cad on master.
2. Open Codecov master tree page and verify source commit moved forward.
3. If not moved:
   - add CODECOV_TOKEN secret in GitHub settings,
   - re-run workflow_dispatch,
   - inspect Codecov upload step logs.
4. In RTD project admin, repair webhook secret and send a test delivery from GitHub.
5. Recheck README badge outputs on the repository homepage.

### Environment Notes
- Local venv used for validation: .venv-assess (Python 3.14.4).
- Working tree contains one untracked file at handoff time: tmp_cds.fa (not committed).

## 2026-05-19 13:56 UTC - Priority 0 complete, Priority 1 executed and verified

### Snapshot
- Branch: master
- New commit: 6d49334
- Objective: complete Priority 0 checks, execute Priority 1 remediation, and re-verify Codecov ingestion.

### What Was Done
1. Re-verified Priority 0 baseline
   - GitHub Actions run #57 on commit 45ac920 completed successfully.
   - Codecov web tree remained stale even though commit rows were appearing.
2. Executed Priority 1 remediation
   - Updated `.github/workflows/build.yml` to generate `coverage.xml` in build1.
   - Switched Codecov upload input from `.coverage` to `coverage.xml`.
   - Commit: `6d49334` (pushed to master).
3. Re-verified after Priority 1
   - Run #58 (head `6d49334`) completed successfully.
   - Codecov commit endpoint for `6d49334` shows `state: complete` and parsed totals.
   - Codecov branch API for `master` now reports head commit `6d49334` with 34.19% coverage.

### Notes
- The public Codecov branch web tree page may lag or cache stale values briefly.
- API endpoints reflected the corrected, current state before the tree page visually refreshed.