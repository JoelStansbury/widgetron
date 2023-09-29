from hashlib import sha256
import json
import os
import platform
import re
import shutil
import sys
import zipfile
from pathlib import Path
from subprocess import Popen, PIPE

import yaml

from .parse_args import CONFIG
from .utils import call, copy, copytree, move, cd, SETTINGS, zipdir


from .jinja_functions import render_templates


CMDS = []

HERE = Path(__file__).parent
PYTHON = Path(sys.executable)
CONDA_PREFIX = PYTHON.parent
REQUIRED_PKGS = [
    "jupyterlab",
    "conda",
]  # menuinst is added separately for exact version

NPM = shutil.which("npm")
CONDA = shutil.which("mamba") or shutil.which("conda")
JAKE = shutil.which("jake")
CONSTRUCTOR = shutil.which("constructor")

WIN = platform.system() == "Windows"
LINUX = platform.system() == "Linux"
OSX = platform.system() == "Darwin"
CONDA_ENV = {}  # once condarc is created, it will be added to this env

assert NPM, f"Missing dependencies (npm)"
assert CONDA, "Could not find conda"

DEFAULT_SERVER_COMMAND = ["jupyter", "lab", "--no-browser"]

if WIN:
    DEFAULT_ICON = (HERE / "icons/widgetron.ico").absolute()
elif LINUX:
    DEFAULT_ICON = (HERE / "icons/widgetron.png").absolute()
elif OSX:
    DEFAULT_ICON = (HERE / "icons/widgetron.icns").absolute()
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


def _install_missing_pkgs(env, pkgs, channels) -> int:
    cmd = [CONDA, "install", "--prefix", str(env), "-y", *pkgs, "-c", *channels]
    return call(cmd)


def parse_arguments():
    kwargs = CONFIG
    kwargs["dependencies"] = kwargs.get("dependencies", [])
    kwargs["channels"] = kwargs.get(
        "channels", ["https://conda.anaconda.org/conda-forge"]
    )
    kwargs["local_channels"] = [x for x in kwargs["channels"] if x.startswith("file:")]
    kwargs["non_local_channels"] = [x for x in kwargs["channels"] if not x.startswith("file:")]

    assert isinstance(kwargs["channels"], list), f"Channels should be a list. Not ({type(kwargs['channels'])})"
    if kwargs["python_version"] == "auto":
        kwargs["python_version"] = ".".join(list(map(str, sys.version_info[:2])))
    if isinstance(kwargs["dependencies"], str):
        kwargs["dependencies"] = kwargs["dependencies"].strip().split()
    if isinstance(kwargs["channels"], str):
        kwargs["channels"] = kwargs["channels"].strip().split()
    if kwargs["license_file"]:
        kwargs["license_file"] = str(Path(kwargs["license_file"]).absolute())
    if "environment_yaml" in kwargs:
        print("found env.yml")
        with open(kwargs["environment_yaml"], "r") as f:
            _env = yaml.safe_load(f)
        kwargs["dependencies"] += _env["dependencies"]
        kwargs["channels"] += _env["channels"]
    SETTINGS["DRY_RUN"] = kwargs["dry_run"]
    kwargs["temp_files"] = Path("widgetron_temp_files").resolve()
    SETTINGS["log"] = Path(kwargs["temp_files"]).absolute() / "commands.txt"

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
    kwargs["icon_name"] = Path(kwargs["icon"]).name

    kwargs["name"] = Path(kwargs["notebook"]).stem

    pat = re.compile(r"[^a-zA-Z0-9]")
    kwargs["name_nospace"] = pat.sub("_", kwargs["name"])

    kwargs["filename"] = Path(kwargs["notebook"]).name

    if "explicit_lock" in kwargs:
        assert (
            "environment" not in kwargs
        ), "cannot provide env and lock at the same time."

        if not kwargs["skip_sbom"]:
            assert JAKE, "Missing jake. Cannot produce conda sbom."

            # Generate SBOM (because we can)
            cmd = [
                JAKE,
                "sbom",
                "-t=CONDA",
                f"-f={kwargs['explicit_lock']}",
                "--output-format=json",
                f"-o={Path(kwargs['outdir'])/'conda-sbom.json'}",
            ]
            call(cmd)

        # Build the environment and reference the env directory
        call(
            [
                CONDA,
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
                _install_missing_pkgs(env, missing_pkgs, kwargs["channels"])
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
    kwargs["channels"] = [kwargs["pkg_output_dir"].as_uri(), *kwargs["channels"]]
    kwargs["local_channels"].append(kwargs["pkg_output_dir"].as_uri())
    return kwargs


def copy_notebook(kwargs):
    # Copy notebook into template
    # Check filetype
    server = kwargs["temp_files"] / "server"
    dest = server / "widgetron_app/notebooks"
    nb = Path(kwargs["notebook"])

    if kwargs.get("license_file"):
        copy(kwargs["license_file"], server / "LICENSE.txt")

    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir()

    if nb.is_file():
        assert nb.suffix.lower() == ".ipynb", f"{nb} is not a notebook"
        copy(nb, dest / nb.name)
    else:
        dest = dest / nb.stem
        if dest.exists():
            shutil.rmtree(dest)
            CMDS.append(["rm", "-r", str(dest)])
        assert list(nb.glob("*.ipynb")), f"No notebooks found in {nb}"
        copytree(nb, dest)


def package_electron_app(kwargs):
    icon = Path(kwargs["icon"]).absolute()
    cwd = Path().absolute()
    try:
        cd(kwargs["temp_files"] / "electron")
        Path("build").mkdir(exist_ok=True)
        # assert icon.suffix.lower() == ".png", "WIP: only png currently supported"
        copy(str(icon), f"build/icon{icon.suffix}")

        call([NPM, "install", ".", "--no-optional"])

        call([NPM, "run", "build"])

        if not kwargs["skip_sbom"]:
            sbom = Path(kwargs["outdir"]) / "npm-sbom.json"
            cmd = [
                NPM,
                "run",
                "lock",
                "--",
                "--output-format",
                "json",
                "--output-file",
                f"{sbom}",
            ]
            call(cmd)

        if OSX or LINUX:
            dist = "dist"
        elif WIN:
            dist = "dist/win-unpacked"

        cd(dist)

        if OSX or LINUX:
            src = list(Path().glob("widgetron*.zip"))[0]
            dst = "../../server/widgetron_app"
            move(src, dst / src)
        elif WIN:
            zipdir(".", "../../../server/widgetron_app/ui.zip")
    finally:
        cd(cwd)


def copy_icon(kwargs):
    icon = Path(kwargs["icon"])
    copy(str(icon), kwargs["temp_files"] / f"recipe/{icon.name}")
    kwargs["icon_name"] = icon.name


def get_conda_build_args(recipe_dir: Path, output_dir: Path) -> list[str]:
    cmd = [
        "boa",
        "build",
        str(recipe_dir.resolve()),
        "--no-test",
        "--output-folder",
        str(output_dir.resolve()),
        "--skip-existing",
    ]

    return cmd


def build_sdist_package(kwargs) -> int:
    srcdir = kwargs["temp_files"] / "server"
    cmd = ["python", "setup.py", "sdist"]
    return call(cmd, cwd=str(srcdir))


def get_conda_build_env(kwargs) -> dict[str, str]:
    env = dict(**os.environ)
    if not SETTINGS["DRY_RUN"]:
        sdist = next((kwargs["temp_files"] / "server/dist").glob("*.tar.gz"))
        env.update(
            SDIST_URL=sdist.as_uri(), SDIST_SHA256=sha256(sdist.read_bytes()).hexdigest(),
            CONDARC = kwargs["CONDARC"],
        )
    return env


def build_conda_package(kwargs) -> int:
    dir = kwargs["temp_files"] / "recipe"
    rc = call(
        get_conda_build_args(dir, kwargs["pkg_output_dir"]),
        env=get_conda_build_env(kwargs),
    )

    if (not rc) and "environment" in kwargs:
        # TODO: move this to a better function
        if _is_installed(kwargs["environment"], "widgetron_app"):
            call(
                [
                    CONDA,
                    "remove",
                    "--prefix",
                    str(kwargs["environment"]),
                    "widgetron_app",
                    "-y",
                ]
            )
        cmd = [
            CONDA,
            "install",
            "--prefix",
            str(kwargs["environment"]),
            "widgetron_app",
            "-y",
            "-c",
            kwargs["pkg_output_dir"].as_uri(),
            *(["--no-shortcuts"] if WIN else []),
            "--force-reinstall",
        ]

        rc = call(cmd)
    return rc


def build_installer(kwargs):
    dir = kwargs["temp_files"] / "constructor"
    env = dict(**os.environ)
    env.update(CONDARC = kwargs["CONDARC"])
    cmd = [CONSTRUCTOR, str(dir), "--output-dir", str(kwargs["outdir"])]
    return call(cmd, env=env)


def cli():
    kwargs = parse_arguments()

    render_templates(**kwargs)
    kwargs["CONDARC"] = str(kwargs["temp_files"] / "condarc.yml")

    copy_notebook(kwargs)
    copy_icon(kwargs)

    if kwargs["template_only"]:
        sys.exit(0)

    package_electron_app(kwargs)
    rc = build_sdist_package(kwargs)
    rc = rc or build_conda_package(kwargs)
    rc = rc or build_installer(kwargs)

    sys.exit(rc)


if __name__ == "__main__":
    cli()
