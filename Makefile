.PHONY: venv run clean

venv:
	python3 -m venv venv
	./venv/bin/pip install -r requirements.txt --extra-index-url https://pypi.org/simple

run: venv
	PYTHONPATH=src ./venv/bin/python3 -m stortrooper_editor.main

clean:
	rm -rf venv
	find . -type d -name "__pycache__" -exec rm -rf {} +

test: venv
	PYTHONPATH=src ./venv/bin/pytest tests
