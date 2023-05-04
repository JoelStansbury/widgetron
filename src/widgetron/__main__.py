import json
import os
import platform
import re
import shutil
import sys
import zipfile
from pathlib import Path
from subprocess import check_call, Popen, PIPE

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
REQUIRED_PKGS = ["jupyterlab", "conda"]

WIN = platform.system() == "Windows"
LINUX = platform.system() == "Linux"
OSX = platform.system() == "Darwin"

CONDA_BUILD = "conda-mambabuild {} -c https://conda.anaconda.org/conda-forge --no-test --no-verify --output-folder {}"
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
    "license_file": lambda x: Path(x).absolute(),
    "batch_mode": str,
    "signing_identity_name": str,
    "welcome_image": lambda x: Path(x).absolute(),
    "header_image": lambda x: Path(x).absolute(),
    "default_image_color": str,
    "welcome_image_text": str,
    "header_image_text": str,
    "nsis_template": lambda x: Path(x).absolute(),
    "default_prefix": str,
    "default_prefix_domain_user": str,
    "default_prefix_all_users": str,
    "environment": lambda x: Path(x).absolute(),
}


def _validate_env(env):
    missing = []
    for pkg in REQUIRED_PKGS:
        if not _is_installed(env, pkg):
            missing.append(pkg)
    if WIN:
        if not _is_installed(env, "menuinst"):
            missing.append("menuinst >=1.4.17")
    return missing


def _is_installed(env, library):
    CONDA = shutil.which("conda")
    cmd = f"{CONDA} list --prefix {env} -f {library} --no-pip --json".split()
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    output, err = p.communicate()
    return bool(json.loads(output))


def _install_missing_pkgs(env, pkgs):
    CONDA = shutil.which("conda")
    check_call(
        [CONDA, "install", "--prefix", str(env), "-y", *pkgs, "-c", "conda-forge"]
    )


def parse_arguments():
    kwargs = CONFIG
    kwargs["dependencies"] = kwargs.get("dependencies", [])
    kwargs["channels"] = kwargs.get(
        "channels", ["https://conda.anaconda.org/conda-forge"]
    )

    if isinstance(kwargs["dependencies"], str):
        kwargs["dependencies"] = kwargs["dependencies"].strip().split()
    if isinstance(kwargs["channels"], str):
        kwargs["channels"] = kwargs["channels"].strip().split()

    elif "environment_yaml" in kwargs:
        with open(kwargs["environment_yaml"], "r") as f:
            _env = yaml.safe_load(f)
        kwargs["dependencies"] += _env["dependencies"]
        kwargs["channels"] += _env["channels"]

    kwargs["server_command"] = kwargs.get("server_command", DEFAULT_SERVER_COMMAND)
    if isinstance(kwargs["server_command"], str):
        kwargs["server_command"] = kwargs["server_command"].strip().split()

    # cli.py template requires executable and cli args to be separated.
    if kwargs["server_command"][0] == "jupyter":  # "jupyter lab"
        kwargs["server_executable"] = "-".join(kwargs["server_command"][:2])
        kwargs["server_command_args"] = kwargs["server_command"][2:]
    elif "jupyter-" in kwargs["server_command"][0]:  # "jupyter-lab"
        kwargs["server_executable"] = kwargs["server_command"][0]
        kwargs["server_command_args"] = kwargs["server_command"][1:]
    else:
        raise ValueError(
            "server command did not follow expected syntax ('jupyter-cmd' or 'jupyter cmd')"
        )

    kwargs["url_whitelist"] = kwargs.get("url_whitelist", [])
    if isinstance(kwargs["url_whitelist"], str):
        kwargs["url_whitelist"] = kwargs["url_whitelist"].strip().split()

    kwargs["domain_whitelist"] = kwargs.get("domain_whitelist", [])
    if isinstance(kwargs["domain_whitelist"], str):
        kwargs["domain_whitelist"] = kwargs["domain_whitelist"].strip().split()

    assert isinstance(kwargs["server_command"], list)
    assert "version" in kwargs

    kwargs["icon"] = kwargs.get("icon", DEFAULT_ICON)

    kwargs["name"] = Path(kwargs["notebook"]).stem

    pat = re.compile(r"[^a-zA-Z0-9]")
    kwargs["name_nospace"] = pat.sub("_", kwargs["name"])

    kwargs["icon_name"] = Path(kwargs["icon"]).name
    kwargs["temp_files"] = Path("widgetron_temp_files")
    kwargs["filename"] = Path(kwargs["notebook"]).name

    if "explicit_lock" in kwargs:
        assert (
            "environment" not in kwargs
        ), "cannot provide env and lock at the same time."

        # Generate SBOM (because we can)
        cmd = [
            "jake",
            "sbom",
            "-t=CONDA",
            f"-f={kwargs['explicit_lock']}",
            "--output-format=json",
            f"-o={Path(kwargs['outdir'])/'conda-sbom.json'}",
        ]
        check_call(cmd)

        # Build the environment and reference the env directory
        check_call(
            [
                "conda",
                "create",
                "--file",
                kwargs["explicit_lock"],
                "--prefix",
                kwargs["temp_files"] / ".env",
            ]
        )
        kwargs["environment"] = kwargs["temp_files"] / ".env"

    if "environment" in kwargs:
        env = kwargs["environment"]
        missing_pkgs = _validate_env(env)
        if missing_pkgs:
            print(
                "Error: Explicit environment is missing the following required packages"
            )
            for m in missing_pkgs:
                print(f"  - {m}")
            inp = input(
                f"Would you like to install them to {env} from conda-forge (y/n)? "
            )
            if inp.lower() in ["y", "yes"]:
                _install_missing_pkgs(env, missing_pkgs)
            else:
                sys.exit()

    kwargs["constructor_params"] = {
        p: CONSTRUCTOR_PARAMS[p](kwargs[p]) for p in CONSTRUCTOR_PARAMS if p in kwargs
    }

    if "pkg_output_dir" not in kwargs:
        kwargs["pkg_output_dir"] = (
            Path(kwargs["temp_files"]) / "conda_build"
        ).absolute()
    else:
        kwargs["pkg_output_dir"] = Path(kwargs["pkg_output_dir"]).absolute()
    kwargs["channels"].append(f"file:///{kwargs['pkg_output_dir']}")
    return kwargs


def copy_source_code(kwargs):
    # Copy python source into template package
    # notebook dir already exists due to debug notebook
    dest = kwargs["temp_files"] / "server/widgetron_app/notebooks"
    # TODO: alter dest if kwargs["notebook"] is a directory

    if "python_source" in kwargs:
        if Path(kwargs["python_source"]).is_dir():
            dest = dest / Path(kwargs["python_source"]).stem
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(kwargs["python_source"], dest)
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
        dest = dest / nb.stem
        if dest.exists():
            shutil.rmtree(dest)
        assert list(nb.glob("*.ipynb")), f"No notebooks found in {nb}"
        shutil.copytree(nb, dest)


def package_electron_app(kwargs):
    icon = Path(kwargs["icon"]).absolute()
    cwd = Path().absolute()

    os.chdir(str(kwargs["temp_files"] / "electron"))
    Path("build").mkdir(exist_ok=True)
    # assert icon.suffix.lower() == ".png", "WIP: only png currently supported"
    shutil.copy(str(icon), f"build/icon{icon.suffix}")

    check_call("npm install .", shell=True)
    sbom = Path(kwargs["outdir"]) / "npm-sbom.json"
    check_call(
        "npm run build",
        shell=True,
    )
    cmd = [
        "npm",
        "run",
        "lock",
        "--",
        "--output-format",
        "json",
        "--output-file",
        f"{sbom}",
    ]
    check_call(cmd, shell=True)

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
    check_call(CONDA_BUILD.format(dir, kwargs["pkg_output_dir"]), shell=True)
    if "environment" in kwargs:
        check_call(
            [
                "conda",
                "run",
                "--prefix",
                kwargs["environment"],
                "conda",
                "install",
                "-y",
                "widgetron_app",
                "-c",
                f"file:///{Path(kwargs['pkg_output_dir']).absolute()}",
                "--no-shortcuts",
                "--force-reinstall",
            ]
        )


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
