.PHONY: install test run docker-build docker-up docker-down

install:
	pip install -r requirements.txt

test:
	python -m unittest discover -s tests

run:
	@if [ -z "$(TARGET)" ]; then \
		echo "Usage: make run TARGET=https://example.com"; \
		exit 1; \
	fi
	python -m watchtower.main -t $(TARGET)

docker-build:
	docker-compose build

docker-up:
	docker-compose up

docker-down:
	docker-compose down
