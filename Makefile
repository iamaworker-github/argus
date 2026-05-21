# =============================================================================
# Argus Makefile
# =============================================================================
# Usage:
#   make build        Build Docker image
#   make run          Run Argus CLI
#   make shell        Open bash in container
#   make api          Start REST API server
#   make repl         Start interactive REPL
#   make scan T=url   Scan a target (e.g., make scan T=https://example.com)
#   make full         Run with all sidecar services (redis, neo4j)
#   make clean        Clean up containers and data
# =============================================================================

# Config
TARGET ?= https://example.com
MODE ?= pentest
DEPTH ?= quick
API_PORT ?= 8484
VERSION ?= latest

.PHONY: build run shell api repl scan full clean logs

# Build
build:
	docker build -t argus:$(VERSION) .
	@echo "✅ Argus image built: argus:$(VERSION)"

build-full:
	docker build -t argus:$(VERSION) --target=full .
	@echo "✅ Argus full image built: argus:$(VERSION)"

# Run
run:
	docker run --rm -it \
		-v argus_data:/root/.argus \
		-v $(PWD)/argus_results:/app/argus_results \
		-e LLM_API_KEY=$(LLM_API_KEY) \
		argus:$(VERSION) "$(CMD)"

scan:
	docker run --rm -it \
		-v argus_data:/root/.argus \
		-v $(PWD)/argus_results:/app/argus_results \
		-v $(PWD):/app/target:ro \
		-e LLM_API_KEY=$(LLM_API_KEY) \
		-e STRIX_LLM=$(STRIX_LLM) \
		argus:$(VERSION) strix --target $(TARGET) --mode $(MODE) -m $(DEPTH)

# Services
api:
	docker compose --profile api up -d
	@echo "✅ API: http://localhost:$(API_PORT)"

repl:
	docker run --rm -it \
		-v argus_data:/root/.argus \
		-e LLM_API_KEY=$(LLM_API_KEY) \
		argus:$(VERSION) repl

shell:
	docker run --rm -it \
		-v argus_data:/root/.argus \
		-v $(PWD):/app/target:ro \
		argus:$(VERSION) bash

# Full stack
full:
	docker compose --profile full up -d
	@echo "✅ Full stack running (Argus + Redis + Neo4j)"

# Utils
logs:
	docker compose logs -f

clean:
	docker compose down -v
	docker rm -f argus 2>/dev/null || true
	@echo "✅ Cleaned up"

install:
	@echo "Installing Argus..."
	pip install -r requirements.txt
	pip install -e .
	@echo "✅ Argus installed. Run: argus --help"

test:
	docker run --rm -v $(PWD):/app argus:$(VERSION) python -m pytest tests/ -v

# Help
help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Build targets:"
	@echo "  build        Build Docker image"
	@echo "  build-full   Build full image with security tools"
	@echo ""
	@echo "Run targets:"
	@echo "  scan T=url   Run scan against target"
	@echo "  api          Start REST API server"
	@echo "  repl         Start interactive REPL"
	@echo "  shell        Open bash in container"
	@echo ""
	@echo "Config:"
	@echo "  TARGET       Target URL (default: https://example.com)"
	@echo "  MODE         pentest/osint/ctf (default: pentest)"
	@echo "  DEPTH        quick/standard/deep (default: quick)"
	@echo "  LLM_API_KEY  Your LLM API key"
	@echo "  STRIX_LLM    Model (default: openai/gpt-4o)"
