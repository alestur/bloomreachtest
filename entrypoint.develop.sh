#!/bin/sh


gunicorn runserver:app_factory -w 1 -k aiohttp.GunicornWebWorker --reload --bind 0.0.0.0:8000
