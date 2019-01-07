#!/bin/bash
FUNCTION_NAME="summariseSlice"

zip -FS /tmp/lambda-$FUNCTION_NAME.zip lambda_function.py bcftools
