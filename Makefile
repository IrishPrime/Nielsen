all: wheel sdist

clean:
	-rm -rf **/*.pyc
	-rm -rf **/__pycache__/*
	-rm -rf dist/*

# Run the pickler script, which makes actual calls to remote APIs and pickles
# the responses so further tests can be run against the saved responses rather
# than making new queries every time.
pickle:
	./bin/pickler.py

sdist: nielsen/*.py pyproject.toml README.md
	uv build --sdist

wheel: nielsen/*.py pyproject.toml README.md
	uv build --wheel

# Install and source the completion script for zsh
zsh:
	nielsen --install-completion zsh
	$(shell source ~/.zfunc/_nielsen)

.PHONY: all
.PHONY: clean
.PHONY: pickle
.PHONY: sdist
.PHONY: wheel
.PHONY: zsh
