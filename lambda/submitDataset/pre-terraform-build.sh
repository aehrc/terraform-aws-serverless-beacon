#!/bin/bash
FUNCTION_NAME="submitDataset"

zip -FS $FUNCTION_NAME.zip lambda_function.py api_response.py
