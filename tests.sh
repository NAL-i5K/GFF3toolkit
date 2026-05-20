#!/usr/bin/env bash
set -euo pipefail

python tests.py
python -m unittest discover -s tests/unit -p 'test_*.py'

# Cleanup temporary artifacts that can be produced during local test runs.
rm -f out_user_defined.fa tests/__init__.py
