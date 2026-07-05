.PHONY: setup dev logs shell test train-ml seed migrate

# Bootstrap the project from scratch
setup:
	@echo "→ Copying environment file..."
	cp .env.example .env
	@echo "→ Building Docker images..."
	docker compose build
	@echo "→ Starting services..."
	docker compose up -d db redis
	@sleep 5
	@echo "→ Running database migrations..."
	docker compose run --rm api python manage.py migrate
	@echo "→ Creating superuser (admin@codesentinel.dev / Admin123!)..."
	docker compose run --rm api python manage.py shell -c \
		"from apps.users.models import User; User.objects.create_superuser('admin@codesentinel.dev','Admin123!')"
	@echo "→ Seeding demo data..."
	docker compose run --rm api python manage.py seed_demo_data
	@echo "✓ Setup complete. Run 'make dev' to start."

# Start all services
dev:
	docker compose up

# Tail logs from all services
logs:
	docker compose logs -f

# Open a Django shell inside the running api container
shell:
	docker compose exec api python manage.py shell

# Run the full test suite
test:
	docker compose run --rm api pytest --cov=apps --cov-report=term-missing --cov-fail-under=80

# Run ML training pipeline (requires datasets to be downloaded first)
train-ml:
	docker compose run --rm api python ml/training/train.py

# Seed demo data
seed:
	docker compose run --rm api python manage.py seed_demo_data

# Run database migrations
migrate:
	docker compose run --rm api python manage.py migrate

# Generate new migrations after model changes
makemigrations:
	docker compose run --rm api python manage.py makemigrations

# Stop all services
stop:
	docker compose stop

# Stop and remove all containers and volumes
clean:
	docker compose down -v
