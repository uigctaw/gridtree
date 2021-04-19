#!/bin/bash
set -e

./run_tests.sh
./flake8.sh
./mypy.sh
./bandit.sh
./spelling.sh
