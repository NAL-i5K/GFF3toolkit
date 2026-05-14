#!/usr/bin/env bash
set -euo pipefail

python tests.py
python -m unittest discover -s tests/unit -p 'test_*.py'
