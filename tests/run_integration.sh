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

# Docker on non-linux runs in a vm. If you are not running on localhost, set DOCKER_IP as an ENV
# Using docker-machine, running tox via "DOCKER_IP=$(docker-machine ip testenv) tox" is one option
# to do that.
export DOCKER_IP=${DOCKER_IP:-localhost}

SOLR_CONTAINER=$(docker run -P -d mitlibraries/oastats-solr)
MONGO_CONTAINER=$(docker run -P -d mongo)

trap cleanup EXIT

# There's no easy way to tell when a container is ready. A more elegant
# solution with a loop would be better here, but this hack works for now.
sleep 5

MONGO_PORT=$(docker port $MONGO_CONTAINER 27017/tcp | cut -d':' -f2)
SOLR_PORT=$(docker port $SOLR_CONTAINER 8983/tcp | cut -d':' -f2)

export MONGO_URI=$DOCKER_IP:$MONGO_PORT
export SOLR_URI=$DOCKER_IP:$SOLR_PORT

if [ $COVERAGE -eq 1 ]; then
    py.test --cov=pipeline --cov-append tests/integration --tb=short
else
    py.test tests/integration --tb=short
fi
