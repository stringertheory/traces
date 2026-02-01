.PHONY: install
install: ## Install the poetry environment and install the pre-commit hooks
	@echo "🚀 Creating virtual environment using pyenv and poetry"
	@poetry install
	@poetry run pre-commit install
	@poetry shell

.PHONY: check
check: ## Run code quality tools.
	@echo "🚀 Linting code: Running pre-commit"
	@poetry run pre-commit run -a
	# @echo "🚀 Static type checking: Running mypy"
	# @poetry run mypy
	# @echo "🚀 Checking for obsolete dependencies: Running deptry"
	# @poetry run deptry traces
	@echo "🚀 Check if using dev dependencies outside of tests marked external"
	@./.check_external_deps.sh

.PHONY: test
test: ## Test the code with pytest
	@echo "🚀 Testing code: Running pytest"
	@poetry run pytest --cov --cov-config=pyproject.toml --cov-report=xml

.PHONY: test-only-main
test-only-main: ## Test the code with pytest
	@echo "🚀 Testing code: Running pytest with only main dependencies"
	@poetry run pytest $$(ls tests/*.py | grep -v external)

.PHONY: build
build: clean-build ## Build wheel file using poetry
	@echo "🚀 Creating wheel file"
	@poetry build

.PHONY: clean-build
clean-build: ## clean build artifacts
	@rm -rf dist

.PHONY: publish
publish: ## publish a release to pypi.
	@echo "🚀 Publishing: Dry run."
	@poetry config pypi-token.pypi $(POETRY_PYPI_TOKEN_PYPI)
	@poetry publish --dry-run
	@echo "🚀 Publishing."
	@poetry publish

.PHONY: build-and-publish
build-and-publish: build publish ## Build and publish.

.PHONY: docs-test
docs-test: ## Test if documentation can be built without warnings or errors
	# @poetry run mkdocs build -s
	@poetry run sphinx-build docs docs/_build/html

.PHONY: docs
docs: ## Build and serve the documentation
	# @poetry run mkdocs serve -a localhost:8002
	@poetry run sphinx-autobuild --port 8002 docs docs/_build/html

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
