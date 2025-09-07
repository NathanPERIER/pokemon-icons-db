PYTHON = python3

VENV_DIR = ./venv
VENV_PYTHON = ${VENV_DIR}/bin/python3


.PHONY: venv pip check mermaid

venv:
	${PYTHON} -m venv ${VENV_DIR}
	make pip

pip:
	${VENV_PYTHON} -m pip install -U -r ./requirements.txt

check:
	${VENV_PYTHON} scripts/check.py

spritesheets:
	${VENV_PYTHON} scripts/generate_spritesheets.py

html:
	${VENV_PYTHON} scripts/generate_html.py

markdown:
	${VENV_PYTHON} scripts/generate_markdown.py

mermaid:
	${VENV_PYTHON} scripts/generate_mermaid.py

