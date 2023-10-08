test:
	-coverage run --omit nielsen/logging.py -m unittest discover
	-coverage html --omit nielsen/logging.py --skip-empty nielsen/*.py
	-coverage report --omit nielsen/logging.py --skip-empty nielsen/*.py

# Run the pickler script, which makes actual calls to remote APIs and pickles
# the responses so further tests can be run against the saved responses rather
# than making new queries every time.
pickle:
	./bin/pickler.py

.PHONY: test
.PHONY: pickle
