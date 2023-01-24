test:
	-coverage run -m unittest discover
	-coverage html nielsen/*.py
	-coverage report nielsen/*.py

pickle:
	./bin/pickler.py

.PHONY: test
.PHONY: pickle
