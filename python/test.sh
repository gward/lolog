#!/bin/sh

set -e

dir=$(dirname $0)
set -x
flake8 $dir
mypy $dir --exclude python/intercept-test.py
PYTHONPATH=$dir TZ=UTC pytest --cov=lolog --cov-report=term-missing $dir/tests
