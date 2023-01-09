import os
import platform
import sys
from pathlib import Path


# Location of environment file
ENV_FILE = "environment.yaml"

# Path to environment
ENV_PATH = "./.venv"

# Path to source code (with setup.py)
SRC = "./src"


USE_MAMBA = True
PLATFORM = platform.system()
PYTHON = sys.executable
os.environ["CONDA_ALWAYS_YES"] = "true"

# Tasks to run during `doit` (with no args)
Path("logs").mkdir(exist_ok=True)
DOIT_CONFIG = {
    'default_tasks': ['update_deps', 'install_src'],
    'dep_file': 'logs/doit-db.json',
}

class CONDA:
    _conda = "mamba" if USE_MAMBA else "conda"
    update = f'{_conda} env update -f "{ENV_FILE}" -p "{ENV_PATH}"'
    activate = f'{_conda} activate "{ENV_PATH}"'
    build = f"{activate} && conda mambabuild recipe --output-folder dist/conda -c conda-forge"

try:
    with open("../keys/pypi", "r") as f:
        PYPI_USERNAME, PYPI_PASSWORD = f.read().strip().split()
except Exception as e:
    print("Could not find PyPi credentials... PyPi Distribution Disabled")

class PyPi:
    update_build_deps = "python -m pip install --upgrade build twine"
    build = f"python -m build --outdir dist/pypi {SRC}"
    upload = f"python -m twine upload --repository pypi dist/pypi/* -u {PYPI_USERNAME} -p {PYPI_PASSWORD}"
    distribute = f"{CONDA.activate} && {update_build_deps} && {build} && {upload}"

sort_imports = f"isort {SRC}"
black_format = f"black {SRC} -l 79"
CLEAN = f"{CONDA.activate} && {sort_imports} && {black_format}"

def _do(*args, **kwargs):
    kwargs["actions"] = args
    return kwargs

def task_update_deps():
    return _do(
        CONDA.update,
        file_dep=[ENV_FILE]  # Skip if file has not changed
    )

def task_install_src():
    return _do(f"{CONDA.activate} && pip install -e {SRC}")

def task_lab():
    return _do(f"{CONDA.activate} && jupyter lab")

def task_publish():
    return _do(CLEAN, PyPi.distribute)

def task_condabuild():
    return _do(CLEAN, CONDA.build)
