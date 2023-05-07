#!/bin/sh

set -e

dirs="lolog tests"
set -x
flake8 $dirs
mypy $dirs --exclude tests/intercept-test.py
PYTHONPATH=$dir TZ=UTC pytest --cov=lolog --cov-report=term-missing tests
