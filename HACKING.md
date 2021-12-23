# Working on lolog

If you wish to modify lolog and contribute to it, here's how to get started.

First, create a virtualenv:

    python3 -m venv <dir>

Don't forget to activate the virtualenv for every development session!

Then install development dependencies:

    pip install -e '.[dev]'

That done, you can run the unit tests with

    ./python/test.sh
