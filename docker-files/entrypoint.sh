#!/bin/sh

# Ensure the SQLite file exists
if [ ! -d "/usr/src/app/data" ]; then
  mkdir -p /usr/src/app/data
fi

if [ ! -f "/usr/src/app/data/db.sqlite3" ]; then
  echo "Creating SQLite database file..."
  touch /usr/src/app/data/db.sqlite3
  chmod 666 /usr/src/app/data/db.sqlite3
fi

echo "${0}: running migrations."
python manage.py migrate

echo "${0}: collecting statics."
python manage.py collectstatic --noinput

echo "${0}: importing groups & permissions."
python manage.py import_groups

exec "$@"
