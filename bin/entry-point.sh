#!/usr/bin/env bash

gunicorn hsv_dot_beer.wsgi --log-file - &
celery -A hsv_dot_beer worker -l info &
celery -A hsv_dot_beer beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
