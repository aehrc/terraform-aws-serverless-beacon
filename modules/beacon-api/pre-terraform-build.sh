#!/bin/bash
for dir in "$(pwd)"/lambda/*/
do
    cd "${dir}"
    ./pre-terraform-build.sh
done
