

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
	docker-compose up --remove-orphans

stop:
	docker-compose down -v

clean:
	docker-compose rm --force
	rm -rf metadata/*
	rm -rf keys/*