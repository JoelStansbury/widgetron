import json
from pathlib import Path
from urllib.parse import unquote, urlparse
import sys
from warnings import warn

import yaml

from ..constants import CONDA, WIN
from .shell import SHELL


def is_installed(env: Path | str, library: str) -> bool:
    return bool(
        json.loads(
            SHELL.check_output(
                [
                    CONDA,
                    "list",
                    "--prefix",
                    str(env),
                    "-f",
                    library,
                    "--no-pip",
                    "--json",
                ]
            )
        )
    )


def install_many(
    env, pkgs: list[tuple[str, str]], channels: list[str] | str = "conda-forge"
) -> int:
    channels = [channels] if isinstance(channels, str) else channels
    pkgs: list[str] = [f"{p} {v}" if v else p for p, v in pkgs]
    cmd = [
        CONDA,
        "install",
        "--prefix",
        str(env),
        "-y",
        *pkgs,
        *sum([["-c", channel] for channel in channels], start=[])
        * (["--no-shortcuts"] if WIN else []),
    ]
    return SHELL.call(cmd)


def install_one(env, package: str, channel: str, **package_attrs) -> int:
    url = explicit_url(package, channel, **package_attrs)
    channels = [channels] if isinstance(channels, str) else channels
    pkgs: list[str] = [f"{p} {v}" if v else p for p, v in pkgs]
    cmd = [
        CONDA,
        "install",
        "--prefix",
        str(env),
        "-y",
        url,
        *(["--no-shortcuts"] if WIN else []),
    ]
    return SHELL.call(cmd)


def ensure_not_installed(env: Path | str, library: str) -> int:
    if is_installed(env, library):
        if WIN:
            msg = f"""
                Found existing installation of {library} in {env}.
                On windows this may prompt for admin privleges in order to remove any shortcuts that
                could exist (this may cause timeout errors on CI).
                This may happen locally if you try to build multiple time.
            """
            warn(msg)
        return SHELL.call(
            [
                CONDA,
                "remove",
                "--prefix",
                str(env),
                library,
                "-y",
            ]
        )


def is_local_channel(x: str | Path) -> bool:
    if str(x).startswith("file:"):
        return True
    if Path(x).exists() and list(Path(x).glob("channeldata.json")):
        return True
    if x == "local":
        return True
    return False


def validate_local_channel(x: str):
    if x == "local":
        p = Path(sys.prefix) / "conda-bld"
    else:
        p = unquote(urlparse(str(x)).path)
        p = p.strip("/")  # remove leading "/"
        p = Path(p)
    assert (
        p.exists()
    ), f"Channel was provided as a local file uri ({x}), but the nothing was found at ({p})"
    assert list(
        p.glob("channeldata.json")
    ), f"Local channel ({x}) has no 'channeldata.json'."


def format_local_channel(x: str | Path) -> str:
    if x == "local":
        return "local"
    if str(x).startswith("file:"):
        return x
    return Path(x).absolute().as_uri()


def add_package_to_lock(
    filename: Path | str, package: str, channel: str, **package_attrs
) -> str:
    filename = Path(filename)
    lock_str = filename.read_text()
    assert is_lock_file(
        content=lock_str
    ), "Not a valid lock file. Missing '@EXPLICIT' line."
    url = explicit_url(package, channel, **package_attrs)
    filename.write_text(lock_str.rstrip() + f"\n{url}\n")


def add_package_to_yaml(
    filename: Path | str, package: str, channel: str, **package_attrs
) -> str:
    filename = Path(filename)
    package = f"{channel}::{package}"
    if "version" in package_attrs:
        package = f"{package} {package_attrs['version']}"
    data = yaml.safe_load(filename.read_text())
    if package not in data["dependencies"]:
        data["dependencies"].append(package)
    if channel not in data["channels"]:
        data["channels"] = [channel, *data["channels"]]
    filename.write_text(yaml.safe_dump(data))


def is_lock_file(filename=None, content=None):
    content = content or Path(filename).read_text()
    l = [x.strip() for x in content[:150].split("\n")]
    return "@EXPLICIT" in l


def find_env(env: str) -> str:
    if Path(env).is_dir() and Path(env).exists():
        return str(Path(env).absolute())
    conda_config = json.loads(
        SHELL.check_output(["conda", "config", "--show", "--json"])
    )
    matches = []
    for envs_dir in conda_config["envs_dirs"]:
        p = Path(envs_dir)
        matches += [str(p / x) for x in p.glob(env)]

    env_as_prefix = str(Path(env).absolute())
    envs_dirs_str = "\n  ".join(conda_config["envs_dirs"])
    assert (
        matches
    ), f"'{env_as_prefix}' does not exist and no envs with the name '{env}' were found in any of the default locations:\n  {envs_dirs_str}"

    # This check probably is not necessary. I think conda will not allow this in the first place.
    matches_str = "\n  ".join(matches)
    assert (
        len(matches) == 1
    ), f"Found multiple envs with the name '{env}':\n  {matches_str}"
    return matches[0]


def explicit_url(package: str, channel: str, **package_attrs):
    """
    package_attrs:
        'arch',
        'build',
        'build_number',
        'channel',
        'constrains',
        'depends',
        'fn',
        'md5',
        'name',
        'noarch',
        'package_type',
        'platform',
        'sha256',
        'size',
        'subdir',
        'timestamp',
        'url',
        'version'
    """
    info = json.loads(
        SHELL.check_output([CONDA, "search", "-c", channel, package, "--json"])
    )
    print(info)
    if package_attrs:
        for k, v in package_attrs.items():
            info["package"] = [x for x in info["package"] if x[k] == v]
    pkg = info[package][0]
    return f"{pkg['url']}#{pkg['md5']}"
