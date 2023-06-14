#! /usr/bin/env sh
set -e
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-2278}
DCRX_BOOT_WAIT=${DCRX_BOOT_WAIT:-10}
UVICORN_WORKERS=${UVICORN_WORKERS:-2}

PRE_START_PATH=${PRE_START_PATH:-/prestart.sh}

sleep $DCRX_BOOT_WAIT

echo "Checking for script in $PRE_START_PATH"
if [ -f $PRE_START_PATH ] ; then
    echo "Running script $PRE_START_PATH"
    /bin/sh "$PRE_START_PATH"
else 
    echo "There is no script $PRE_START_PATH"
fi
# Start Gunicorn
exec dcrx-kv server run --workers $UVICORN_WORKERS --host $HOST --port $PORT