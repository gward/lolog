#!/bin/sh

set -e

dir=$(dirname $0)
set -x
flake8 $dir
mypy $dir
PYTHONPATH=$dir TZ=UTC pytest --cov=lolog --cov-report=term-missing $dir/tests
