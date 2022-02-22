# YOCO
[![PyPI Release](https://github.com/roym899/yoco/actions/workflows/publish_release.yaml/badge.svg)](https://github.com/roym899/yoco/actions/workflows/publish_release.yaml) [![PyTest](https://github.com/roym899/yoco/actions/workflows/pytest.yaml/badge.svg)](https://github.com/roym899/yoco/actions/workflows/pytest.yaml) [![Docs](https://github.com/roym899/yoco/actions/workflows/build_docs.yaml/badge.svg)](https://github.com/roym899/yoco/actions/workflows/build_docs.yaml)

YOCO is a minimalistic YAML-based configuration system for Python.
Visit the [YOCO documentation](https://roym899.github.io/yoco/) for detailed usage instructions and API reference.


## Installation
```bash
pip install yoco
```

## Development
- Use `pip install -e .` to install the package in editable mode
- Use `pip install -r requirements-dev.txt` to install dev tools
- Use `pytest -rf --cov=yoco --cov-report term-missing tests/` to run tests and check code coverage
