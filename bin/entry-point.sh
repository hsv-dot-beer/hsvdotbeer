#!/usr/bin/env bash

pipenv run gunicorn hsv_dot_beer.wsgi --log-file - &
pipenv run celery -A hsv_dot_beer worker -l info &
pipenv run celery -A hsv_dot_beer beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
