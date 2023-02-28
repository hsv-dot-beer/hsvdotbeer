#!/usr/bin/env bash

npm run build
pipenv run python manage.py migrate
pipenv run python manage.py collectstatic --noinput
pipenv run gunicorn hsv_dot_beer.wsgi --log-file - &
pipenv run celery -A hsv_dot_beer worker -l info -c 2 --beat --scheduler django_celery_beat.schedulers:DatabaseScheduler -O fair
