release: cd main && python manage.py migrate && python manage.py collectstatic --noinput
web: cd main && gunicorn setup.wsgi:application --bind 0.0.0.0:$PORT --workers 3
worker: cd main && celery -A setup worker -l info
beat: cd main && celery -A setup beat -l info