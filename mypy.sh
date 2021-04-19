#!/bin/bash
poetry run python -m mypy --show-error-codes gridtree
poetry run python -m mypy --show-error-codes tests
