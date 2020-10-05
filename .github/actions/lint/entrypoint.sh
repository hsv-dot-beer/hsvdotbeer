#!/bin/bash -l

set -e
pwd
flake8
black --check .
