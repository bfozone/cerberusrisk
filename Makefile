.PHONY: up down build rebuild logs logs-api logs-dash ps clean test dev prod

up:
	podman compose up -d

dev:
	podman compose up -d --force-recreate

prod:
	podman compose -f compose.yml up -d --force-recreate

down:
	podman compose down

build:
	podman compose build
	podman compose up -d --force-recreate

rebuild:
	podman compose build --no-cache
	podman compose up -d --force-recreate

logs:
	podman compose logs -f

logs-api:
	podman logs -f cerberusrisk_api_1

logs-dash:
	podman logs -f cerberusrisk_dashboard_1

ps:
	podman ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

clean:
	podman compose down -v
	podman image prune -f

test:
	@echo "Testing API..."
	@curl -s http://localhost:8000/health | python3 -m json.tool
	@echo "\nTesting portfolios..."
	@curl -s http://localhost:8000/api/portfolios | python3 -m json.tool

shell-api:
	podman exec -it cerberusrisk_api_1 /bin/bash

shell-db:
	podman exec -it cerberusrisk_postgres_1 psql -U cerberus -d cerberusrisk
