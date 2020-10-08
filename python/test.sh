#!/bin/sh

set -e

dir=$(dirname $0)
flake8 $dir
PYTHONPATH=$dir pytest $dir/tests
