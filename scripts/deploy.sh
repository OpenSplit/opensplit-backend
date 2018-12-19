#! /usr/bin/env bash
set -eu

STAGE="$1"

ssh travis@"$APP_SERVER" "./update-backend.sh $STAGE"
