#!/bin/sh


gunicorn runserver:app_factory -w $WORKERS -k aiohttp.GunicornWebWorker --bind 0.0.0.0:8000
