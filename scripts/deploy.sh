#! /usr/bin/env bash
set -eu

if [ "$1" == "production" ]; then
	TAG="latest"
elif [ "$1" == "staging" ]; then
	TAG="development"
else
	echo "Unknown environment: "$1
	exit 1
fi
docker login -u "$DOCKER_USERNAME" -p "$DOCKER_PASSWORD"
docker push $IMAGE:$TAG

