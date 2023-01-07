import os
import platform
import sys
from pathlib import Path

# Tasks to run during `doit` (with no args)
Path("logs").mkdir(exist_ok=True)
DOIT_CONFIG = {
    'default_tasks': ['update_deps', 'install_src'],
    'dep_file': 'logs/doit-db.json',
}


# Use mamba by default
USE_MAMBA = True

# Automatically agree to conda actions
os.environ["CONDA_ALWAYS_YES"] = "true"

# Location of environment file
ENV_FILE = "environment.yaml"

# Path to environment
ENV_PATH = "./.venv"

try:
    with open("../keys/pypi", "r") as f:
        PYPI_USERNAME, PYPI_PASSWORD = f.read().strip().split()
except Exception as e:
    print("Could not find PyPi credentials... PyPi Distribution Disabled")
    PYPI_USERNAME, PYPI_PASSWORD = "", ""

PLATFORM = platform.system()
PYTHON = sys.executable

class CONDA:
    _conda = "mamba" if USE_MAMBA else "conda"
    update = f'{_conda} env update -f "{ENV_FILE}" -p "{ENV_PATH}"'
    activate = f'{_conda} activate "{ENV_PATH}"'
    build = f"{activate} && conda mambabuild recipe --output-folder dist/conda -c conda-forge"

class PyPi:
    update_build_deps = "python -m pip install --upgrade build twine"
    build = "python -m build --outdir dist/pypi"
    upload = f"python -m twine upload --repository pypi dist/pypi/* -u {PYPI_USERNAME} -p {PYPI_PASSWORD}"
    distribute = f"{update_build_deps} && {build} && {upload}"

# Formatting
sort_imports = "isort ipypdf/ tests/"
black_format = "black ipypdf/ tests/ -l 79"
CLEAN = f"{CONDA.activate} && {sort_imports} && {black_format}"

def task_update_deps():
    return {
        "actions": [
            CONDA.update
        ],
        "file_dep": [ENV_FILE],
    }

def task_install_src():
    return {
        "actions": [
            f"{CONDA.activate} && pip install -e ./src"
        ]
    }

def task_lab():
    return {
        "actions": [
            f"{CONDA.activate} && jupyter lab"
        ]
    }


# def task_publish():
#     return {
#         "actions": [
#             f"{CONDA.activate} && {CLEAN} && {PyPi.distribute}"
#         ],
#         "verbosity": 2,
#     }


def task_condabuild():
    return {
        "actions": [f"{CLEAN} && {CONDA.build}"],
    }
