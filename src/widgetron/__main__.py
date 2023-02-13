import argparse
import os
import platform
import re
import shutil
import sys
from pathlib import Path
from subprocess import call

from .jinja_functions import render_templates

HERE = Path(__file__).parent
PYTHON = Path(sys.executable)
CONDA_PREFIX = PYTHON.parent

WIN = platform.system() == "Windows"
LINUX = platform.system() == "Linux"
OSX = platform.system() == "Darwin"

INSTALL_ELECTRON = "npm install --save-dev electron"
INSTALL_ELECTRON_PACKAGER = "npm install --save-dev electron-packager"
PACKAGE_ELECTRON_APPLICATION = 'npx electron-packager . --out=../server/widgetron_app --ignore=node_modules --icon="{}"'.format
CONDA_BUILD = "conda-mambabuild {} -c conda-forge"

if WIN:
    DEFAULT_ICON = HERE / "icons/widgetron.ico"
elif LINUX:
    DEFAULT_ICON = HERE / "icons/widgetron.png"
elif OSX:
    DEFAULT_ICON = HERE / "icons/widgetron.icns"
else:
    raise OSError(f"Unknown platform {platform.system()}")

parser = argparse.ArgumentParser(
    prog="widgetron",
    description="Creates an electron app for displaying the output cells of an interactive notebook.",
)

src_desc = """
This is a shortcut to avoid needing to build a conda package for your source code.
Widgetron is basically a big jinja template, if your notebook has `from my_package import my_widget`
then you would pass C:/path/to/my_package, and the directory will by copied recursively
into a package shell immediately next to the notebook.
"""

arguments = [
    [["file"], {}, "Path to notebook to convert. (must be .ipynb)"],
    [
        ["-deps", "--dependencies"],
        dict(nargs="+", default=[]),
        "List of conda-forge packages required to run the widget (pip packages are not supported).",
    ],
    [
        ["-c", "--channels"],
        dict(nargs="+", default=["conda-forge"]),
        "List of conda channels required to find specified packages. Order is obeyed, 'local' is always checked first. Default= ['conda-forge',]",
    ],
    [
        ["-p", "--port"],
        dict(default="8866"),
        "4-digit port number on which the notebook will be hosted.",
    ],
    [
        ["-n", "--name"],
        {},
        "Name of the application (defaults to the notebook name).",
    ],
    [["-o", "--outdir"], dict(default="."), "App version number."],
    [["-v", "--version"], dict(default=1), ""],
    [["-src", "--python_source_dir"], {}, src_desc],
    [
        ["-icon", "--icon"],
        dict(default=DEFAULT_ICON),
        "Icon for app. (windows->.ico, linux->.png/.svg, osx->.icns)",
    ],
]

for flags, kwargs, desc in arguments:
    kwargs["help"] = desc
    parser.add_argument(*flags, **kwargs)


def parse_arguments():
    kwargs = parser.parse_args().__dict__

    if kwargs["name"] is None:
        kwargs["name"] = Path(kwargs["file"]).stem

    pat = re.compile(r"[^a-zA-Z0-9]")
    kwargs["name_nospace"] = pat.sub("_", kwargs["name"])

    kwargs["icon_name"] = Path(kwargs["icon"]).name
    kwargs["temp_files"] = Path(kwargs["outdir"]) / "widgetron_temp_files"
    kwargs["filename"] = Path(kwargs["file"]).name
    return kwargs


def copy_source_code(kwargs):
    # Copy python source into template package
    if kwargs["python_source_dir"]:
        if Path(kwargs["python_source_dir"]).is_dir():
            shutil.copytree(
                kwargs["python_source_dir"],
                kwargs["temp_files"]
                / "server/widgetron_app"
                / Path(kwargs["python_source_dir"]).stem,
            )
        elif Path(kwargs["python_source_dir"]).is_file():
            shutil.copy(
                kwargs["python_source_dir"],
                kwargs["temp_files"] / "server" / "widgetron_app",
            )


def copy_notebook(kwargs):
    # Copy notebook into template
    # Check filetype
    nb = Path(kwargs["file"])
    if nb.is_file():
        assert nb.suffix.lower() == ".ipynb", f"{nb} is not a notebook"
        shutil.copy(nb, kwargs["temp_files"] / "server/widgetron_app")
    else:
        assert list(nb.glob("*.ipynb")), f"No notebooks found in {nb}"
        assert not kwargs[
            "python_source_dir"
        ], "-src may only be provided if -f is a single .ipynb file"
        shutil.copytree(
            nb, kwargs["temp_files"] / f"server/widgetron_app/{nb.stem}"
        )


def package_electron_app(kwargs):
    icon = Path(kwargs["icon"]).absolute()
    cwd = Path().absolute()

    os.chdir(str(kwargs["temp_files"] / "electron"))

    call("npm install .", shell=True)
    call(
        PACKAGE_ELECTRON_APPLICATION(icon),
        shell=True,
    )
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
    call(f"constructor {dir}", shell=True)


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
