web: cd backend && python manage.py migrate --run-syncdb && python scripts/collect_static_for_deploy.py && gunicorn vhbridge.wsgi:application --bind 0.0.0.0:$PORT --workers 2
