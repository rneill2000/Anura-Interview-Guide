web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn interview_guide_project.wsgi --bind 0.0.0.0:$PORT --timeout 180 --workers 2
