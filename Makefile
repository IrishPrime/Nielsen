test:
	-coverage run -m unittest discover
	-coverage html nielsen/*.py
	-coverage report nielsen/*.py

.PHONY: test
