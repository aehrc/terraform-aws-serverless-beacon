#!/bin/bash
FUNCTION_NAME="summariseDataset"

zip -FS /tmp/lambda-$FUNCTION_NAME.zip lambda_function.py
