import argparse
import sys
import os
import platform
from pathlib import Path
import shutil
from subprocess import call

from .jinja_functions import render

WIDGETRON = Path(__file__).parent
PYTHON = Path(sys.executable)
CONDA_PREFIX = PYTHON.parent
WIN = platform.system() == "Windows"

INSTALL_ELECTRON = "npm install --save-dev electron"
INSTALL_ELECTRON_PACKAGER = "npm install --save-dev electron-packager"
PACKAGE_ELECTRON_APPLICATION = "npx electron-packager {} --out={}"
CONDA_BUILD = "conda-mambabuild {} -c conda-forge"

parser = argparse.ArgumentParser(
    prog = 'widgetron',
    description = 'Creates an electron app for displaying the output cells of an interactive notebook.',
    epilog = 'example usage: widgetron -f=my_notebook.ipynb'
)
parser.add_argument(
    '-f', 
    '--file', 
    required=True, 
    help="Path to notebook to convert. (must be .ipynb)"
)
parser.add_argument(
    '-deps', 
    '--dependencies', 
    required=False, 
    nargs='+',
    help="List of conda-forge packages required to run the widget (pip packages are not supported).",
    default=[]
)
parser.add_argument(
    '-p', 
    '--port', 
    required=False, 
    help="4-digit port number on which the notebook will be hosted.", 
    default="8866"
)
parser.add_argument(
    '-n', 
    '--name', 
    required=False, 
    help="Name of the application (defaults to the notebook name)."
)
parser.add_argument(
    '-o', 
    '--outdir', 
    required=False, 
    help="Output directory.", 
    default=str(Path())
)
parser.add_argument(
    '-v', 
    '--version', 
    required=False, 
    help="App version number.", 
    default=1
)
parser.add_argument(
    '-env', 
    '--conda_prefix', 
    required=False, 
    help="Environment to package with the installer (defaults to the active conda environment).", 
    default=str(CONDA_PREFIX)
)
src_desc = """
Use with caution.
This is a shortcut to avoid needing to build a conda package for your source code.
Widgetron is basically a big jinja template, if your notebook has `from my_package import my_widget`
then you would pass C:/path/to/my_package, and the directory will by copied recursively
into a package shell immediately next to the notebook.
"""
parser.add_argument(
    '-src', 
    '--python_source_dir',
    required=False,
    help=src_desc, 
)
parser.add_argument(
    '--icon', 
    required=False, 
    help="Icon for app."
)

def cli():
    kwargs = parser.parse_args().__dict__

    
    if not kwargs["file"].endswith(".ipynb"):
        print(f"ERROR: file must have (.ipynb) extension. Not ({Path(args['file']).suffix})")
        return
    else:
        # Use notebook name if not defined
        kwargs["name"] = kwargs["name"] or Path(kwargs["file"]).stem.replace(" ", "_")
        kwargs["temp_files"] = Path(kwargs["outdir"]) / "widgetron_temp_files"
        kwargs["filename"] = Path(kwargs["file"]).name

        # Insert KWARGS into template files
        render(**kwargs)

        # Copy python source into template
        if kwargs["python_source_dir"]:
            if Path(kwargs["python_source_dir"]).is_dir():
                shutil.copytree(
                    kwargs["python_source_dir"],
                    kwargs["temp_files"] / "server" / "widgetron_app" / Path(kwargs["python_source_dir"]).stem
                )
            elif Path(kwargs["python_source_dir"]).is_file():
                shutil.copy(
                    kwargs["python_source_dir"],
                    kwargs["temp_files"] / "server" / "widgetron_app"
                )
        
        # Copy notebook into template
        shutil.copy(
            kwargs["file"],
            kwargs["temp_files"] / "server" / "widgetron_app"
        )


        # Compile electron app
        cwd = Path().absolute()
        os.chdir(str(kwargs["temp_files"] / "electron"))  # cd to the app dir

        call("npm install", shell=WIN)
        call(
            PACKAGE_ELECTRON_APPLICATION.format(
                ".",  # source files
                '../server/widgetron_app',  # destination
            ) + (f" --icon={cwd / kwargs['icon']}" if kwargs['icon'] else ""),
            shell=WIN
        )
        os.chdir(str(cwd))  # go back

        # Build conda-package
        call(
            CONDA_BUILD.format(
                kwargs['temp_files'] / 'recipe',  # recipe dir
                shell=WIN
            )
        )

        # Build conda-package
        call(
            CONDA_BUILD.format(
                kwargs['temp_files'] / 'recipe',  # recipe dir
                shell=WIN
            )
        )

        # Build installer
        call(f"constructor {kwargs['temp_files'] / 'constructor'}", shell=WIN)

if __name__=="__main__":
    cli()