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

cleanup () {
    docker stop $SOLR_CONTAINER && docker rm $SOLR_CONTAINER
    docker stop $MONGO_CONTAINER && docker rm $MONGO_CONTAINER
}

SOLR_CONTAINER=$(docker run -P -d mitlibraries/oastats-solr)
MONGO_CONTAINER=$(docker run -P -d mongo)

trap cleanup EXIT

# There's no easy way to tell when a container is ready. A more elegant
# solution with a loop would be better here, but this hack works for now.
sleep 5

export MONGO_PORT=$(docker port $MONGO_CONTAINER 27017/tcp | cut -d':' -f2)
export SOLR_PORT=$(docker port $SOLR_CONTAINER 8983/tcp | cut -d':' -f2)

if [ $COVERAGE -eq 1 ]; then
    py.test --cov=pipeline --cov-append tests/integration --tb=short
else
    py.test tests/integration --tb=short
fi
