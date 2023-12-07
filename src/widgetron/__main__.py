from hashlib import sha256
import os
import re
import shutil
import sys
from pathlib import Path

from .utils.conda import uninstall_widgetron, create_sbom

from .globals import CONFIG
from .constants import (
    CONSTRUCTOR,
    CONDA,
    TEMP_DIR,
    WIN,
    LINUX,
    OSX,
    NPM,
    DEFAULT_SERVER_COMMAND,
    DEFAULT_ICON,
)
from .globals import CONSTRUCTOR_PARAMS
from .utils.shell import SHELL
from .utils.jinja_functions import render_templates


def parse_arguments():
    kwargs = CONFIG

    if kwargs["python_version"] == "auto":
        kwargs["python_version"] = ".".join(list(map(str, sys.version_info[:2])))
    if kwargs["license_file"]:
        kwargs["license_file"] = str(Path(kwargs["license_file"]).resolve())

    SHELL.mock = kwargs["dry_run"]
    SHELL.log = kwargs.get("command_log", None)

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

    assert isinstance(kwargs["server_command"], list)
    assert "version" in kwargs

    kwargs["icon"] = kwargs.get("icon", DEFAULT_ICON)
    kwargs["icon_name"] = Path(kwargs["icon"]).name
    kwargs["name"] = Path(kwargs["notebook"]).stem

    pat = re.compile(r"[^a-zA-Z0-9]")
    kwargs["name_nospace"] = pat.sub("_", kwargs["name"])

    kwargs["filename"] = Path(kwargs["notebook"]).name

    kwargs["temp_dir"] = Path(kwargs.get("temp_dir", TEMP_DIR)).resolve()
    kwargs["pkg_output_dir"] = str(
        kwargs.get("pkg_output_dir", kwargs["temp_dir"] / "conda-bld")
    )

    CONSTRUCTOR_PARAMS.name = kwargs["name"]
    CONSTRUCTOR_PARAMS.version = kwargs["version"]
    CONSTRUCTOR_PARAMS.validate()

    return kwargs


def copy_notebook(kwargs):
    # Copy notebook into template
    # Check filetype
    server = kwargs["temp_dir"] / "server"
    dest = server / "widgetron_app/notebooks"
    nb = Path(kwargs["notebook"])

    if kwargs.get("license_file"):
        SHELL.copy(kwargs["license_file"], server / "LICENSE.txt")

    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir()

    if nb.is_file():
        assert nb.suffix.lower() == ".ipynb", f"{nb} is not a notebook"
        SHELL.copy(nb, dest / nb.name)
    else:
        dest = dest / nb.stem
        if dest.exists():
            shutil.rmtree(dest)
        assert list(nb.glob("*.ipynb")), f"No notebooks found in {nb}"
        ignore = [".ipynb_checkpoints", "__pycache__"]
        SHELL.copytree(src=nb, dst=dest, ignore=shutil.ignore_patterns(*ignore))


def package_electron_app(kwargs):
    icon = Path(kwargs["icon"]).resolve()
    cwd = Path().resolve()
    try:
        SHELL.cd(kwargs["temp_dir"] / "electron")
        Path("build").mkdir(exist_ok=True)
        # assert icon.suffix.lower() == ".png", "WIP: only png currently supported"
        SHELL.copy(str(icon), f"build/icon{icon.suffix}")

        SHELL.call([NPM, "install", ".", "--no-optional"])

        SHELL.call([NPM, "run", "build"])

        env = os.environ
        env["FETCH_LICENSE"] = "1"

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
            SHELL.call(cmd, env=env)

        if OSX or LINUX:
            dist = "dist"
        elif WIN:
            dist = "dist/win-unpacked"

        SHELL.cd(dist)

        if OSX or LINUX:
            src = list(Path().glob("widgetron*.zip"))[0]
            dst = "../../server/widgetron_app"
            SHELL.move(src, dst / src)
        elif WIN:
            SHELL.zipdir(".", "../../../server/widgetron_app/ui.zip")
    finally:
        SHELL.cd(cwd)


def get_conda_build_args(recipe_dir: Path, output_dir: Path) -> list[str]:
    cmd = [
        "boa",
        "build",
        str(recipe_dir.resolve()),
        "--no-test",
        "--output-folder",
        str(output_dir),
        "--skip-existing",
    ]

    return cmd


def build_sdist_package(kwargs) -> int:
    srcdir = kwargs["temp_dir"] / "server"
    cmd = ["python", "setup.py", "sdist"]
    return SHELL.call(cmd, cwd=str(srcdir))


def get_conda_build_env(kwargs) -> dict[str, str]:
    env = dict(**os.environ)
    if not SHELL.mock:
        sdist = next((kwargs["temp_dir"] / "server/dist").glob("*.tar.gz"))
        env.update(
            SDIST_URL=sdist.as_uri(),
            SDIST_SHA256=sha256(sdist.read_bytes()).hexdigest(),
        )

    return env


def build_conda_package(kwargs) -> int:
    dir = kwargs["temp_dir"] / "recipe"
    rc = SHELL.call(
        get_conda_build_args(Path(dir), kwargs["pkg_output_dir"]),
        env=get_conda_build_env(kwargs),
    )
    if CONSTRUCTOR_PARAMS.environment:
        uninstall_widgetron(CONSTRUCTOR_PARAMS.environment)
    CONSTRUCTOR_PARAMS.add_dependency(
        package="widgetron_app",
        channel=kwargs["pkg_output_dir"],
    )
    if (not kwargs["skip_sbom"]) and CONSTRUCTOR_PARAMS.environment_file:
        create_sbom(
            CONSTRUCTOR_PARAMS.environment_file,
            Path(kwargs["outdir"]) / "conda-sbom.json",
        )
    return rc


def build_installer(kwargs):
    dir = CONSTRUCTOR_PARAMS.path
    cmd = [CONSTRUCTOR, str(dir), "--output-dir", str(kwargs["outdir"])]
    return SHELL.call(cmd)


def cli():
    kwargs = parse_arguments()

    render_templates(**kwargs)

    copy_notebook(kwargs)

    if kwargs["template_only"]:
        sys.exit(0)

    package_electron_app(kwargs)
    rc = build_sdist_package(kwargs)
    rc = rc or build_conda_package(kwargs)
    rc = rc or build_installer(kwargs)

    sys.exit(rc)


if __name__ == "__main__":
    cli()
