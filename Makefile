.PHONY: all clean build serve format lint

all: build

clean:
	rm -rf _site
	rm -rf .generator_cache

build:
	uv run build-blog

serve:
	uv run serve-blog

format:
	uv run ruff format generator

lint:
	uv run ruff check generator
