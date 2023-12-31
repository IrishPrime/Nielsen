test:
	-coverage run -m pytest test.py
	-coverage html --skip-empty nielsen/*.py
	-coverage report --skip-empty nielsen/*.py

# Run the pickler script, which makes actual calls to remote APIs and pickles
# the responses so further tests can be run against the saved responses rather
# than making new queries every time.
pickle:
	./bin/pickler.py

# Install and source the completion script for zsh
zsh:
	nielsen --install-completion zsh
	$(shell source ~/.zfunc/_nielsen)

.PHONY: test
.PHONY: pickle
.PHONY: zsh
