#!/bin/sh

set -e

flake8 .
PYTHONPATH=$(pwd) pytest tests
