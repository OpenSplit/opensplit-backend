#! /bin/bash

# Build from Dockerfile
docker build -t opensplit/backend .

# Push container to Docker Hub
docker push opensplit/backend

