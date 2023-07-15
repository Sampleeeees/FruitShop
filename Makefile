mr:
	python manage.py makemigrations && python manage.py migrate && python manage.py runserver
r:
	python manage.py runserver
worker:
	celery -A config worker -l INFO
beat:
	celery -A config beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler
startup:
	python manage.py makemigrations
	python manage.py migrate
	python manage.py collectstatic --no-input
	python manage.py create_fruit
	python manage.py create_user
	daphne -b 0.0.0.0 -p 8000 config.asgi:application
down:
	docker compose down -v
build:
	docker compose -f docker-compose.yml up --build