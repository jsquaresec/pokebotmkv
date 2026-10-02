up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

bootstrap:
	docker compose exec bot python scripts/bootstrap.py

seed:
	docker compose exec bot python scripts/seed_data.py

smoke:
	docker compose exec bot python scripts/verify_stack.py

test:
	python -m pytest -q

migrate:
	docker compose run --rm migrator
