import argparse
import json
import os
import platform
import shutil
import sys
from pathlib import Path
from subprocess import call

from .jinja_functions import render_templates

WIDGETRON = Path(__file__).parent
PYTHON = Path(sys.executable)
CONDA_PREFIX = PYTHON.parent
WIN = platform.system() == "Windows"

INSTALL_ELECTRON = "npm install --save-dev electron"
INSTALL_ELECTRON_PACKAGER = "npm install --save-dev electron-packager"
PACKAGE_ELECTRON_APPLICATION = "npx electron-packager . --out=../server/widgetron_app --ignore=node_modules"
CONDA_BUILD = "conda-mambabuild {} -c conda-forge"

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
    [["-icon", "--icon"], {}, "Icon for app. Must be a .ico file"],
]

for flags, kwargs, desc in arguments:
    kwargs["help"] = desc
    parser.add_argument(*flags, **kwargs)


def parse_arguments():
    kwargs = parser.parse_args().__dict__

    if not kwargs["file"].endswith(".ipynb"):
        print("ERROR: file must have (.ipynb) extension.")
        return

    if kwargs["name"] is None:
        kwargs["name"] = Path(kwargs["file"]).stem.replace(" ", "_")

    kwargs["temp_files"] = Path(kwargs["outdir"]) / "widgetron_temp_files"
    kwargs["filename"] = Path(kwargs["file"]).name
    return kwargs


def handle_source_code(kwargs):
    # Copy python source into template
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
    shutil.copy(kwargs["file"], kwargs["temp_files"] / "server/widgetron_app")


def package_electron_app(kwargs):
    cwd = Path().absolute()
    icon = kwargs["icon"]

    if icon is None:
        extra = ""
    else:
        icon = Path(icon).absolute()
        extra = f" --icon={icon}"

    os.chdir(str(kwargs["temp_files"] / "electron"))

    call("npm install .", shell=True)
    call(
        PACKAGE_ELECTRON_APPLICATION + extra,
        shell=True,
    )
    os.chdir(str(cwd))


def create_windows_menu_file(kwargs):
    name = kwargs["name"]
    temp_files = kwargs["temp_files"]

    server = temp_files / "server"
    output = temp_files / "recipe/widgetron_shortcut.json"

    # Locate the executable file for the electron app
    exe = next(server.rglob("*.exe")).relative_to(server)
    install_path = Path("lib/site-packages") / exe

    # Create menuinst description of the shortcut
    data = {
        "menu_name": name,
        "menu_items": [
            {
                "name": name,
                "system": "${ROOT_PREFIX}\\" + "\\".join(install_path.parts),
            }
        ],
    }

    # Export it to the recipe dir for the conda package
    with open(output, "w") as f:
        json.dump(data, f)


def build_conda_package(kwargs):
    dir = kwargs["temp_files"] / "recipe"
    call(CONDA_BUILD.format(dir), shell=True)


def build_installer(kwargs):
    dir = kwargs["temp_files"] / "constructor"
    call(f"constructor {dir}", shell=True)


def cli():
    kwargs = parse_arguments()
    render_templates(**kwargs)
    handle_source_code(kwargs)
    copy_notebook(kwargs)
    package_electron_app(kwargs)
    if WIN: create_windows_menu_file(kwargs)
    build_conda_package(kwargs)
    build_installer(kwargs)


if __name__ == "__main__":
    cli()
