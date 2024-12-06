#!/bin/bash

# HTTP için Gunicorn'u başlat
gunicorn --workers=3 --bind=0.0.0.0:10000 djangoProject.wsgi:application &

# WebSocket için Daphne'yi başlat
daphne -p 8000 djangoProject.asgi:application

