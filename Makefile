test: test-sqlite test-postgres test-flake8

test-sqlite: install-dependencies
	coverage run setup.py test
	coverage report -m --fail-under 65

test-postgres: install-dependencies
	python setup.py test_on_postgres

test-flake8:
	pip install flake8
	flake8 .

install-dependencies:
	pip install -r dev_requirements.txt
