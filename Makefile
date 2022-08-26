

reformat:
	black -l 79 .
	isort -l79 --profile black .

tests:
	tox -r

requirements:
	pipenv lock -r > requirements.txt
	pipenv lock -r -d > requirements-dev.txt

coverage:
	coverage report
	coverage html -i

build-dev:
	docker build -t kaprien-rest-api:dev .

run-dev:
	$(MAKE) build-dev
	docker login ghcr.io
	docker pull ghcr.io/kaprien/kaprien-repo-worker:dev
	docker-compose up --remove-orphans

stop:
	docker-compose down -v

clean:
	$(MAKE) stop
	docker-compose rm --force
	rm -rf ./metadata/*
	rm -rf ./keys/*
	rm -rf ./database/*.sqlite
	rm -rf ./data
	rm -rf ./data_test

purge:
	$(MAKE) clean
	docker rmi kaprien-rest-api_kaprien-rest-api --force