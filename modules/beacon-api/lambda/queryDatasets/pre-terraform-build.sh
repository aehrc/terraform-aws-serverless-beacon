#!/bin/bash
FUNCTION_NAME="queryDatasets"

zip -FS /tmp/lambda-$FUNCTION_NAME.zip lambda_function.py
