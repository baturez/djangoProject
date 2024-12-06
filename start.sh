#!/bin/bash

# HTTP için Gunicorn'u başlat
gunicorn --workers=3 --bind=0.0.0.0:8000 djangoProject.wsgi:application &

# WebSocket için Daphne'yi başlat
daphne --port 10000 --bind 0.0.0.0 djangoProject.asgi:application
