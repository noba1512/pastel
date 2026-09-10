#!/bin/sh
set -e

echo "Aplicando migrations..."
python manage.py migrate --noinput

echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo "Iniciando Django..."
exec python manage.py runserver 0.0.0.0:8000
