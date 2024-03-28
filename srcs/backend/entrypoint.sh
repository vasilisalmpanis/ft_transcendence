#!/bin/sh

set -e 

poetry install --no-root
source .venv/bin/activate
cd transcendence_backend

echo "${0}: running migrations."
python3 manage.py makemigrations --merge
python3 manage.py migrate --noinput

python3 manage.py runworker pong_runner tournament_runner&

# Starting the server
echo "${0}: starting the server."
python3 manage.py runserver 0.0.0.0:8000