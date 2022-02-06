PYTHON ?= ./.venv/bin/python

help:  ## this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

test-server:  ## run test web server
	$(PYTHON) http_server.py

test-curl:  ## send request to server
	curl http://localhost:8000?dir=test\&word=hello
