test:
	-coverage run -m unittest discover
	-coverage html nielsen/*.py
	-coverage report nielsen/*.py

# Run the pickler script, which makes actual calls to remote APIs and pickles
# the responses so further tests can be run against the saved responses rather
# than making new queries every time.
pickle:
	./bin/pickler.py

.PHONY: test
.PHONY: pickle
