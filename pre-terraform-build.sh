#!/bin/bash
for module in "$(pwd)"/modules/*/
do
    cd "${module}"
    ./pre-terraform-build.sh
done
