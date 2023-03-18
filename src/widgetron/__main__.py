import os
import platform
import re
import shutil
import sys
import zipfile
from pathlib import Path
from subprocess import call

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

CONDA_BUILD = "conda-mambabuild {} -c conda-forge"
DEFAULT_SERVER_COMMAND = ["jupyter", "lab", "--no-browser"]

if WIN:
    DEFAULT_ICON = HERE / "icons/widgetron.ico"
    DEFAULT_TARGET = "win"
elif LINUX:
    DEFAULT_ICON = HERE / "icons/widgetron.png"
    DEFAULT_TARGET = "linux"
elif OSX:
    DEFAULT_ICON = HERE / "icons/widgetron.icns"
    DEFAULT_TARGET = "mac"
else:
    raise OSError(f"Unknown platform {platform.system()}")


def parse_arguments():
    kwargs = CONFIG
    kwargs["dependencies"] = kwargs.get("dependencies", [])
    kwargs["channels"] = kwargs.get("channels", [])

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
    elif "environment_yaml" in kwargs:
        with open(kwargs["environment_yaml"], "r") as f:
            _env = yaml.safe_load(f)
        print(f"Searching for dependencies in {kwargs['environment_yaml']}")
        kwargs["dependencies"] += _env["dependencies"]
        print(f"Searching for channels in {kwargs['environment_yaml']}")
        kwargs["channels"] +=  _env["channels"]

    kwargs["server_command"] = kwargs.get("server_command", DEFAULT_SERVER_COMMAND)
    if isinstance(kwargs["server_command"], str):
        kwargs["server_command"]=kwargs["server_command"].strip().split()

    assert isinstance(kwargs["server_command"], list)
    assert "version" in kwargs

    kwargs["icon"] = kwargs.get("icon", DEFAULT_ICON)

    kwargs["name"] = Path(kwargs["notebook"]).stem

    pat = re.compile(r"[^a-zA-Z0-9]")
    kwargs["name_nospace"] = pat.sub("_", kwargs["name"])

    kwargs["icon_name"] = Path(kwargs["icon"]).name
    kwargs["temp_files"] = Path("widgetron_temp_files")
    kwargs["filename"] = Path(kwargs["notebook"]).name

    # https://www.electron.build/multi-platform-build.html
    kwargs["constructor_kwargs"] = {}

    # TODO: include logic for setting installer type
    # https://github.com/conda/constructor/blob/main/CONSTRUCT.md#installer_type
    if "target" in kwargs:
        if kwargs["target"] == "win":
            kwargs["constructor_target"] = "win-64"
            kwargs["electron_target"] = "win"
        if kwargs["target"] == "linux":
            kwargs["constructor_target"] = "linux-64"
            kwargs["electron_target"] = "linux"
        if kwargs["target"] == "mac":
            assert OSX, "Electron-builder can only build mac from a mac"
            kwargs["constructor_target"] = "osx-64"
            kwargs["electron_target"] = "mac"
    else:
        # Leaving constructor_target empty lets constructor infer the best one
        kwargs["electron_target"] = DEFAULT_TARGET
    return kwargs


def copy_source_code(kwargs):
    # Copy python source into template package
    dest = kwargs["temp_files"] / "server/widgetron_app/notebooks"
    dest.mkdir()

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

    call("npm install .", shell=True)
    call(
        "npm run build",
        shell=True,
    )
    if kwargs["electron_target"] == "mac":
        dist = "dist/mac"
    elif kwargs["electron_target"] == "linux":
        dist = "dist/linux-unpacked"
    elif kwargs["electron_target"] == "win":
        dist = "dist/win-unpacked"

    os.chdir(dist)

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
    call(CONDA_BUILD.format(dir), shell=True)


def build_installer(kwargs):
    dir = kwargs["temp_files"] / "constructor"
    dir = dir.absolute()
    os.chdir(kwargs["outdir"])

    platform = f"--platform={kwargs['constructor_target']}" if "constructor_target" in kwargs else ""
    cexe = f"--conda-exe={kwargs['conda_exe']}" if "conda_exe" in kwargs else ""
    call(f"constructor {dir} {platform} {cexe}", shell=True)


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
