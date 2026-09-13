.PHONY: test test-verbose init audit clean help

DB ?= registre.duckdb

help:
	@echo "Registre de continuite gouverne"
	@echo ""
	@echo "  make init         Initialise la base DuckDB"
	@echo "  make test         Lance tous les tests"
	@echo "  make test-verbose Lance tous les tests en mode verbose"
	@echo "  make audit        Audite la chaine de hachage"
	@echo "  make clean        Nettoie les artefacts"

init:
	python3 init_db.py --db $(DB)

test:
	python3 -m pytest tests/ -q

test-verbose:
	python3 -m pytest tests/ -v

audit:
	python3 attest/audit_chain.py --db $(DB) --json

clean:
	find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
