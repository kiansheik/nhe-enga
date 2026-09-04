DOCKER="docker"
IMAGE_NAME="kiansheik/nhe-enga"
TAG_NAME="production"

REPOSITORY=""
FULL_IMAGE_NAME=${IMAGE_NAME}:${TAG_NAME}
PYTHON ?= python3.11
VENV_PYTHON ?= .venv/bin/python
PYTHON_DEPS_STAMP ?= .venv/.requirements-installed
GRAMMAR_DIR := gramatica/docs
VUEPRESS_PUBLIC := $(GRAMMAR_DIR)/src/.vuepress/public
PAGES_BUILD_DIR ?= .pages-build

.PHONY: help setup lint format python-deps node-deps build-wheels grammar-build pages-build deploy-gh-pages push gen_data

help:
	@printf '%s\n' 'Nhe-enga build and deploy commands'
	@printf '%s\n' ''
	@printf '%s\n' 'Start-to-finish flow:'
	@printf '%s\n' '  1. make setup            Install Python and VuePress dependencies for this checkout.'
	@printf '%s\n' '  2. make gen_data         Regenerate Navarro dictionary data and conjugation data.'
	@printf '%s\n' '  3. make pages-build      Build wheels, build grammar, and assemble .pages-build.'
	@printf '%s\n' '  4. make deploy-gh-pages  Rebuild .pages-build and push it to the gh-pages branch.'
	@printf '%s\n' ''
	@printf '%s\n' 'Useful checks:'
	@printf '%s\n' '  make lint                Run Black in check-only mode.'
	@printf '%s\n' '  make format              Run Black and write formatting changes.'
	@printf '%s\n' ''
	@printf '%s\n' 'Individual build targets:'
	@printf '%s\n' '  make python-deps         Create/update .venv from requirements.txt.'
	@printf '%s\n' '  make node-deps           Install gramatica/docs Node dependencies if missing.'
	@printf '%s\n' '  make build-wheels        Build tupi/pydicate sdists and wheels for Pyodide.'
	@printf '%s\n' '  make grammar-build       Build only the VuePress grammar site.'
	@printf '%s\n' ''
	@printf '%s\n' 'Deploy knobs:'
	@printf '%s\n' '  REMOTE=origin GH_PAGES_BRANCH=gh-pages make deploy-gh-pages'
	@printf '%s\n' '  SITE_CNAME=kiansheik.io make pages-build'

setup: python-deps node-deps

lint:
	black --check .

format:
	black .

python-deps: $(PYTHON_DEPS_STAMP)

$(PYTHON_DEPS_STAMP): requirements.txt
	$(PYTHON) -m venv .venv
	$(VENV_PYTHON) -m pip install -r requirements.txt
	touch $(PYTHON_DEPS_STAMP)

node-deps:
	@if [ -d "$(GRAMMAR_DIR)/node_modules" ]; then \
		echo "Node dependencies already installed in $(GRAMMAR_DIR)/node_modules"; \
	else \
		cd "$(GRAMMAR_DIR)" && npm install; \
	fi

build-wheels:
	zsh -c 'cd tupi; $(PYTHON) setup.py sdist bdist_wheel;'
	zsh -c 'cd pydicate; $(PYTHON) setup.py sdist bdist_wheel;'
	mkdir -p $(VUEPRESS_PUBLIC)/pylibs
	cp tupi/dist/tupi-*.whl tupi/dist/tupi-*.tar.gz $(VUEPRESS_PUBLIC)/pylibs/
	cp pydicate/dist/pydicate-*.whl pydicate/dist/pydicate-*.tar.gz $(VUEPRESS_PUBLIC)/pylibs/

grammar-build: node-deps build-wheels
	zsh -c 'cd $(GRAMMAR_DIR); export NODE_OPTIONS=--openssl-legacy-provider; npm run build;'

pages-build:
	scripts/build_pages.sh

deploy-gh-pages:
	scripts/deploy_gh_pages.sh
# 	curl -L -o neologisms.csv "https://docs.google.com/spreadsheets/d/1NH_SgkBYY-vAITMtxrZogzihZGsbhIXCaes6HJrcJww/export?format=csv&sheet=AdminWords"

push:
	make lint
	git add .
	git commit
	git push origin HEAD

gen_data: python-deps
	$(VENV_PYTHON) gen_data.py > docs/tupi_dict_navarro.js
	$(VENV_PYTHON) verbs.py
	cp docs/dict-conjugated.json.gz pydicate/pydicate/lang/tupilang/data/
