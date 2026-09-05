.PHONY: help up down logs seed-db shell-backend shell-frontend restart clean

# This Makefile provides convenient commands for ResolveIQ development

help:
	@echo "ResolveIQ Make Commands"
	@echo "======================="
	@echo "make up              - Start all services with Docker Compose"
	@echo "make down            - Stop all services"
	@echo "make logs            - View logs from all services"
	@echo "make logs-backend    - View backend logs"
	@echo "make logs-frontend   - View frontend logs"
	@echo "make seed-db         - Seed database with demo data"
	@echo "make shell-backend   - Open shell in backend container"
	@echo "make shell-frontend  - Open shell in frontend container"
	@echo "make restart         - Restart all services"
	@echo "make clean           - Stop and remove all containers/volumes"
	@echo "make api-docs        - Open API documentation"

up:
	docker-compose up -d
	@echo "✓ Services started"
	@echo "  Frontend: http://localhost:5173"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"

down:
	docker-compose down

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

seed-db:
	docker-compose exec backend python scripts/seed_db.py

shell-backend:
	docker-compose exec backend bash

shell-frontend:
	docker-compose exec frontend sh

restart:
	docker-compose restart

clean:
	docker-compose down -v
	@echo "✓ All containers and volumes removed"

api-docs:
	open http://localhost:8000/docs || xdg-open http://localhost:8000/docs || start http://localhost:8000/docs

migrate:
	docker-compose exec backend alembic upgrade head

migrate-down:
	docker-compose exec backend alembic downgrade -1

test-backend:
	docker-compose exec backend pytest

test-frontend:
	docker-compose exec frontend npm test

lint-backend:
	docker-compose exec backend ruff check app/
	docker-compose exec backend mypy app/

lint-frontend:
	docker-compose exec frontend npm run lint

format-backend:
	docker-compose exec backend black app/
	docker-compose exec backend ruff check app/ --fix

build:
	docker-compose build

build-frontend:
	docker-compose exec frontend npm run build

status:
	docker-compose ps
