#!/bin/sh

echo "${0}: running migrations."
python manage.py migrate

echo "${0}: collecting statics."
python manage.py collectstatic --noinput

echo "${0}: importing groups & permissions."
python manage.py import_groups

exec "$@"
