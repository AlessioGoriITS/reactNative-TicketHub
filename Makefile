.DEFAULT_GOAL := help

.PHONY: help up down logs build test

help:
	@echo "Available commands:"
	@echo "  make up     - start the complete development stack"
	@echo "  make down   - stop the stack"
	@echo "  make logs   - follow service logs"
	@echo "  make build  - build all Docker images"
	@echo "  make test   - run the backend test suite in Docker"

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs --follow

build:
	docker compose build

test:
	docker compose run --rm backend pytest
