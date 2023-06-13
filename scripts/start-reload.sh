#! /usr/bin/env sh
set -e
DCRX_BOOT_WAIT=${DCRX_BOOT_WAIT:-10}
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-80}
LOG_LEVEL=${LOG_LEVEL:-info}

PRE_START_PATH=${PRE_START_PATH:-/prestart.sh}

sleep $DCRX_BOOT_WAIT

echo "Checking for script in $PRE_START_PATH"
if [ -f $PRE_START_PATH ] ; then
    echo "Running script $PRE_START_PATH"
    . "$PRE_START_PATH"
else 
    echo "There is no script $PRE_START_PATH"
fi
# Start Uvicorn with live reload
exec dcrx-kv server run --reload --host $HOST --port $PORT