
.PHONY: all docs tests clean purge run-dev stop build-dev ft-das ft-signed reformat precommit coverage clone-umbrella help

all: help

reformat:  ## Reformat code with black and isort
	black -l 79 .
	isort -l79 --profile black .

tests:  ## Run all tests
	tox -r

precommit:  ## Install and run pre-commit hooks
	pre-commit install
	pre-commit run --all-files --show-diff-on-failure

coverage:  ## Run tests with coverage
	coverage report
	coverage html -i

build-dev:  ## Build the dev image
	docker build -t repository-service-tuf-api:dev .

run-dev: export WORKER_VERSION = dev
run-dev:  ## Run the development environment
	$(MAKE) build-dev
	docker pull ghcr.io/repository-service-tuf/repository-service-tuf-worker:dev
ifneq ($(DC),)
	docker compose -f docker-compose-$(DC).yml up --remove-orphans
else
	docker compose -f docker-compose.yml up --remove-orphans
endif

stop:  ## Stop the development environment
	docker compose down -v

clean:  ## Clean up the environment
	$(MAKE) stop
	docker compose rm --force

purge:  ## Remove all images and containers
	$(MAKE) clean
	docker rmi repository-service-tuf-api_repository-service-tuf-rest-api --force


docs:  ## Build the documentation
	tox -e docs

clone-umbrella:
	if [ -d rstuf-umbrella ];\
		then \
		cd rstuf-umbrella && git pull;\
	else \
		git clone https://github.com/repository-service-tuf/repository-service-tuf.git rstuf-umbrella;\
	fi

ft-das:
# Use "GITHUB_ACTION" to identify if we are running from a GitHub action.
ifeq ($(GITHUB_ACTION),)
	$(MAKE) clone-umbrella
endif
	docker compose run --env UMBRELLA_PATH=rstuf-umbrella --entrypoint 'bash rstuf-umbrella/tests/functional/scripts/run-ft-das.sh $(CLI_VERSION) $(PYTEST_GROUP) $(SLOW)' --rm repository-service-tuf-api

ft-signed:
# Use "GITHUB_ACTION" to identify if we are running from a GitHub action.
ifeq ($(GITHUB_ACTION),)
	$(MAKE) clone-umbrella
endif
	docker compose run --env UMBRELLA_PATH=rstuf-umbrella --entrypoint 'bash rstuf-umbrella/tests/functional/scripts/run-ft-signed.sh $(CLI_VERSION) $(PYTEST_GROUP) $(SLOW)' --rm repository-service-tuf-api

help:  ## Show this help message
	@echo "Makefile commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'	
	@echo
	@echo "Environment variables:"
	@echo "  DC: docker compose file to use (default: docker-compose.yml)"

