.PHONY: venv install-dev test check catalog create generate check-all

venv:
	python3 -m venv .venv

install-dev:
	python3 -m pip install -r requirements-dev.txt

test:
	python3 -m pytest -q

check-all:
	./scripts/check_all.sh

check:
	python3 check_catalog.py --country us

catalog:
	python3 check_catalog.py --country us

create:
	python3 create_playlist.py

generate:
	python3 generate_playlist.py --help
