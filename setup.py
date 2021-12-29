from setuptools import setup

dev_requires = [
    "flake8 >= 4.0.0",
    "pytest >= 6.0.0",
    "pytest-cov >= 3.0.0",
    "freezegun >= 1.0.0",
]

setup(
    name="lolog",
    version="0.0.1",
    author="Greg Ward",
    author_email="greg@gerg.ca",
    description='low-overhead structured logging library',
    packages=['lolog'],
    package_dir={'lolog': 'python/lolog'},
    install_requires=[],
    extras_require={
        "dev": dev_requires,
    },
)
