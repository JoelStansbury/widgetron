import os
import platform
import re
import shutil
import sys
import zipfile
from pathlib import Path
from subprocess import check_call

import yaml

from .parse_args import CONFIG


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(
                os.path.join(root, file),
                os.path.relpath(os.path.join(root, file), os.path.join(path, "..")),
            )


from .jinja_functions import render_templates

HERE = Path(__file__).parent
PYTHON = Path(sys.executable)
CONDA_PREFIX = PYTHON.parent

WIN = platform.system() == "Windows"
LINUX = platform.system() == "Linux"
OSX = platform.system() == "Darwin"

CONDA_BUILD = "conda-mambabuild {} -c https://conda.anaconda.org/conda-forge --no-test --no-verify"
DEFAULT_SERVER_COMMAND = ["jupyter", "lab", "--no-browser"]

if WIN:
    DEFAULT_ICON = HERE / "icons/widgetron.ico"
elif LINUX:
    DEFAULT_ICON = HERE / "icons/widgetron.png"
elif OSX:
    DEFAULT_ICON = HERE / "icons/widgetron.icns"
else:
    raise OSError(f"Unknown platform {platform.system()}")

# Single valued parameters specific to the construc.yaml file
CONSTRUCTOR_PARAMS = {
    "company": str,
    "installer_filename": str,
    "installer_type": str,
    "license_file": lambda x:Path(x).absolute(),
    "batch_mode": str,
    "signing_identity_name": str,
    "welcome_image": lambda x:Path(x).absolute(),
    "header_image": lambda x:Path(x).absolute(),
    "default_image_color": str,
    "welcome_image_text": str,
    "header_image_text": str,
    "nsis_template": lambda x:Path(x).absolute(),
    "default_prefix": str,
    "default_prefix_domain_user": str,
    "default_prefix_all_users": str
}

def parse_arguments():
    kwargs = CONFIG
    kwargs["dependencies"] = kwargs.get("dependencies", [])
    kwargs["channels"] = kwargs.get("channels", ["https://conda.anaconda.org/conda-forge"])

    if isinstance(kwargs["dependencies"], str):
        kwargs["dependencies"]=kwargs["dependencies"].strip().split()
    if isinstance(kwargs["channels"], str):
        kwargs["channels"]=kwargs["channels"].strip().split()

    if "explicit_lock" in kwargs:
        with open(kwargs["explicit_lock"], "r") as f:
            l = f.readline()
            while "@EXPLICIT" not in l:
                l = f.readline()
            kwargs["dependencies"] += [s.strip() for s in f.readlines()]
        cmd = [
            "jake",
            "sbom",
            "-t=CONDA",
            f"-f={kwargs['explicit_lock']}",
            "--output-format=json",
            f"-o={Path(kwargs['outdir'])/'conda-sbom.json'}"
        ]
        print(cmd)
        check_call(cmd)
    elif "environment_yaml" in kwargs:
        with open(kwargs["environment_yaml"], "r") as f:
            _env = yaml.safe_load(f)
        kwargs["dependencies"] += _env["dependencies"]
        kwargs["channels"] +=  _env["channels"]

    kwargs["server_command"] = kwargs.get("server_command", DEFAULT_SERVER_COMMAND)
    if isinstance(kwargs["server_command"], str):
        kwargs["server_command"]=kwargs["server_command"].strip().split()

    # cli.py template requires executable and cli args to be separated.
    if kwargs["server_command"][0] == "jupyter":  # "jupyter lab"
        kwargs["server_executable"] = '-'.join(kwargs["server_command"][:2])
        kwargs["server_command_args"] = kwargs["server_command"][2:]
    elif 'jupyter-' in kwargs["server_command"][0]:  # "jupyter-lab"
        kwargs["server_executable"] = kwargs["server_command"][0]
        kwargs["server_command_args"] = kwargs["server_command"][1:]
    else:
        raise ValueError(
            "server command did not follow expected syntax ('jupyter-cmd' or 'jupyter cmd')"
        )

    kwargs["url_whitelist"] = kwargs.get("url_whitelist", [])
    if isinstance(kwargs["url_whitelist"], str):
        kwargs["url_whitelist"]=kwargs["url_whitelist"].strip().split()

    kwargs["domain_whitelist"] = kwargs.get("domain_whitelist", [])
    if isinstance(kwargs["domain_whitelist"], str):
        kwargs["domain_whitelist"]=kwargs["domain_whitelist"].strip().split()

    assert isinstance(kwargs["server_command"], list)
    assert "version" in kwargs

    kwargs["icon"] = kwargs.get("icon", DEFAULT_ICON)

    kwargs["name"] = Path(kwargs["notebook"]).stem

    pat = re.compile(r"[^a-zA-Z0-9]")
    kwargs["name_nospace"] = pat.sub("_", kwargs["name"])

    kwargs["icon_name"] = Path(kwargs["icon"]).name
    kwargs["temp_files"] = Path("widgetron_temp_files")
    kwargs["filename"] = Path(kwargs["notebook"]).name

    kwargs["constructor_params"] = {
        p: CONSTRUCTOR_PARAMS[p](kwargs[p])
        for p in CONSTRUCTOR_PARAMS if p in kwargs
    }

    return kwargs


def copy_source_code(kwargs):
    # Copy python source into template package
    # notebook dir already exists due to debug notebook
    dest = kwargs["temp_files"] / "server/widgetron_app/notebooks"
    # TODO: alter dest if kwargs["notebook"] is a directory

    if "python_source" in kwargs:
        if Path(kwargs["python_source"]).is_dir():
            shutil.copytree(
                kwargs["python_source"],
                dest / Path(kwargs["python_source"]).stem,
            )
        elif Path(kwargs["python_source"]).is_file():
            shutil.copy(
                kwargs["python_source"],
                dest,
            )


def copy_notebook(kwargs):
    # Copy notebook into template
    # Check filetype
    dest = kwargs["temp_files"] / "server/widgetron_app/notebooks"
    nb = Path(kwargs["notebook"])

    if nb.is_file():
        assert nb.suffix.lower() == ".ipynb", f"{nb} is not a notebook"
        shutil.copy(nb, dest)
    else:
        assert list(nb.glob("*.ipynb")), f"No notebooks found in {nb}"
        shutil.copytree(nb, dest / nb.stem)


def package_electron_app(kwargs):
    icon = Path(kwargs["icon"]).absolute()
    cwd = Path().absolute()

    os.chdir(str(kwargs["temp_files"] / "electron"))
    os.mkdir("build")
    # assert icon.suffix.lower() == ".png", "WIP: only png currently supported"
    shutil.copy(str(icon), f"build/icon{icon.suffix}")

    check_call("npm install .", shell=True)
    sbom = Path(kwargs['outdir']) / 'npm-sbom.json'
    cmd = [
        "npm", "run", "lock", "--",
        "--output-format", "json",
        "--output-file", f"{sbom}"
    ]
    print(cmd)
    check_call(cmd, shell=True)
    check_call(
        "npm run build",
        shell=True,
    )
    if OSX or LINUX:
        dist = "dist"
    elif WIN:
        dist = "dist/win-unpacked"

    os.chdir(dist)

    if OSX or LINUX:
        src = list(Path().glob("widgetron*.zip"))[0]
        dst = "../../server/widgetron_app"
        print(f"Moving '{src}' to '{dst / src}'")
        shutil.move(src, dst / src)
        assert (dst / src).exists(), "Move Failed"
    elif WIN:
        with zipfile.ZipFile(
            "../../../server/widgetron_app/ui.zip", "w", zipfile.ZIP_DEFLATED
        ) as zipf:
            zipdir(".", zipf)

    os.chdir(str(cwd))


def copy_icon(kwargs):
    icon = Path(kwargs["icon"])
    shutil.copy(str(icon), kwargs["temp_files"] / f"recipe/{icon.name}")
    kwargs["icon"] = icon.name


def build_conda_package(kwargs):
    dir = kwargs["temp_files"] / "recipe"
    check_call(CONDA_BUILD.format(dir), shell=True)


def build_installer(kwargs):
    dir = kwargs["temp_files"] / "constructor"
    check_call(f"constructor {dir} --output-dir {kwargs['outdir']}", shell=True)


def cli():
    kwargs = parse_arguments()

    render_templates(**kwargs)
    package_electron_app(kwargs)

    copy_source_code(kwargs)
    copy_notebook(kwargs)
    copy_icon(kwargs)

    build_conda_package(kwargs)
    build_installer(kwargs)


if __name__ == "__main__":
    cli()
