#!/bin/bash

set -m

# Run the RestAPI ("debug" deployment)
python /code/rest_api.py &

# Wait a bit for the restapi to start-up
sleep 3

# Run the Dash client app ("debug" deployment)
python /code/dash_app.py

fg %1
