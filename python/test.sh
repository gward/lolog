#!/bin/sh

set -e

dir=$(dirname $0)
flake8 $dir
PYTHONPATH=$dir TZ=UTC pytest --cov=lolog --cov-report=term-missing $dir/tests
