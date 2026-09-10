#!/bin/sh
set -e

echo "Aplicando migrations..."
python manage.py migrate --noinput

echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

if [ "${DEBUG:-0}" = "1" ]; then
  echo "Iniciando Django (desenvolvimento)..."
  exec python manage.py runserver 0.0.0.0:8000
fi

echo "Iniciando Gunicorn..."
exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout 60 \
  --access-logfile - \
  --error-logfile -
