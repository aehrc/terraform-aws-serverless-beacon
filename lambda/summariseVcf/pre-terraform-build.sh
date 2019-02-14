#!/bin/bash
FUNCTION_NAME="summariseVcf"

zip -FS $FUNCTION_NAME.zip lambda_function.py bcftools chrom_matching.py lambda_utils.py tabix
