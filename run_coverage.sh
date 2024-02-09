#!/bin/bash

# Exit on any error
set -e

# Run pytest under coverage
coverage run --omit 'tests/*' -m pytest tests/

# Generate coverage report in terminal
coverage report

# Generate HTML coverage report
coverage html

# Open the HTML report in the default web browser (Mac example)
#open htmlcov/index.html
