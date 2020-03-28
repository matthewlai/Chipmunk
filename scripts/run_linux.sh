#!/bin/bash

export FLASK_APP=main.py
export FLASK_ENV=production

# Define these for SSL
export FLASK_RUN_CERT='/path/to/fullchain.pem'
export FLASK_RUN_KEY='/path/to/privatekey.pem'

flask run --host 0.0.0.0
