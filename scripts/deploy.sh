#! /usr/bin/env bash
set -eu

STAGE="$1"

ssh travis@"$APP_SERVER" "./test.sh $STAGE"
