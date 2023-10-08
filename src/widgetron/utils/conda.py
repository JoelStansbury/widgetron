import json
from pathlib import Path
from urllib.parse import unquote, urlparse
import sys

import yaml

from ..constants import CONDA
from .shell import SHELL


def is_installed(env: Path | str, library: str) -> bool:
    return bool(json.loads(SHELL.check_output(
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
    )))


def install(env, pkgs: list[tuple[str, str] | str]) -> int:
    pkgs: list[str] = [f"{p} {v}" if v else p for p, v in pkgs]
    cmd = [CONDA, "install", "--prefix", str(env), "-y", *pkgs, "-c", "conda-forge"]
    return SHELL.call(cmd)


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
    assert p.exists(), f"Channel was provided as a local file uri ({x}), but the nothing was found at ({p})"
    assert list(p.glob("channeldata.json")), f"Local channel ({x}) has no 'channeldata.json'."


def format_local_channel(x: str | Path) -> str:
    if x == "local":
        return "local"
    if str(x).startswith("file:"):
        return x
    return Path(x).absolute().as_uri()


def add_package(env_file_contents: str, package:str, channel:str, **package_attrs) -> str:
    if is_lock_file(content=env_file_contents):
        url = explicit_url(package, channel, **package_attrs)
        return env_file_contents.rstrip() + f"\n{url}\n"
    else:
        data = yaml.safe_load(env_file_contents)
        if package not in data["dependencies"]:
            data["dependencies"].append(package)
        if channel not in data["channels"]:
            data["channels"] = [channel, *data["channels"]]
        return yaml.safe_dump(data)


def is_lock_file(filename=None, content=None):
    content = content or Path(filename).read_text()
    l = [x.strip() for x in content[:150].split("\n")]
    return "@EXPLICIT" in l


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
    info = json.loads(SHELL.check_output([CONDA, "search", "-c", channel, package, "--json"]))
    print(info)
    if package_attrs:
        for k,v in package_attrs.items():
            info["package"] = [x for x in info["package"] if x[k] == v]
    pkg = info[package][0]
    return f"{pkg['url']}#{pkg['md5']}"