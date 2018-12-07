#!/bin/bash
FUNCTION_NAME="performQuery"

zip -FS /tmp/lambda-$FUNCTION_NAME.zip lambda_function.py bcftools
