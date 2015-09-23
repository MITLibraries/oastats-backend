#!/usr/bin/env bash

set -ex

COVERAGE=0

while [ $1 ]
do
    case $1 in
        --cov )
            COVERAGE=1
            ;;
    esac
    shift
done

if [ $COVERAGE -eq 1 ]; then
    py.test --cov=pipeline --cov-append tests
else
    py.test tests
fi
