#!/bin/bash

set -m

# Run the RestAPI ("debug" deployment)
uvicorn rest_api:app --host 0.0.0.0 --port 8001 &

# Wait a bit for the restapi to start-up
sleep 3

# Run the Dash client app ("debug" deployment)
python /code/dash_app.py

fg %1
