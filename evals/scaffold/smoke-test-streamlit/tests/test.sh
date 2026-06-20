#!/bin/bash
# Run pytest verifier. Exit code = pass/fail for inspect-coco.
set -e
pytest /workspace/tests/test_outputs.py -v
