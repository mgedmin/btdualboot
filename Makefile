all: bin/btdualboot

bin/btdualboot: | bin .venv
	.venv/bin/pip install -e .
	ln -sr .venv/bin/btdualboot $@

bin:
	mkdir bin

.venv:
	python3 -m venv .venv
	.venv/bin/pip install -U pip
