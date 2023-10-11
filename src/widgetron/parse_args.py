import argparse
import configparser
import json
import os
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib
import yaml

HERE = Path(__file__).parent
ARGS_FILE = HERE / "args.yml"


parser = argparse.ArgumentParser(
    prog="widgetron",
    description="Creates an app for displaying the output cells of an interactive notebook.",
)


def config_file():
    if Path("setup.cfg").is_file():
        setup_cfg = configparser.ConfigParser()
        with Path("setup.cfg").open("r") as f:
            setup_cfg.read_file(f)
        if "tool.widgetron" in setup_cfg:
            print("Initialize from setup.cfg")
            data = setup_cfg._sections["tool.widgetron"]
            if "channels" in data:
                data["channels"] = json.loads(data["channels"])
            if "dependencies" in data:
                data["dependencies"] = json.loads(data["dependencies"])


    if Path("pyproject.toml").is_file():
        _toml = tomllib.load(Path("pyproject.toml").open("rb"))
        if "tool" in _toml:
            if "widgetron" in _toml["tool"]:
                print("Initialize from pyproject.toml")
                return _toml["tool"]["widgetron"]
    return {}


def config():
    defaults = {}
    with ARGS_FILE.open() as f:
        args = yaml.safe_load(f)
    for k, v in args.items():
        if v.pop("positional", None):
            flags = [k]
        else:
            flags = [f"--{k}"]
        if "flag" in v:
            flags += ["-" + v.pop("flag")]
        if "default" in v:
            defaults[k] = v.pop("default")
        if "action" in v:
            v["action"] = getattr(argparse, v["action"])
        parser.add_argument(*flags, **v)
    kwargs = parser.parse_args()

    # Outdir
    #  If provided to CLI, then relative to CWD
    if kwargs.outdir is not None:
        kwargs.outdir = Path(kwargs.outdir).resolve()
    if kwargs.temp_dir is not None:
        kwargs.temp_dir = Path(kwargs.temp_dir).resolve()
    #  If unspecified, then CWD
    defaults["outdir"] = Path(defaults["outdir"]).resolve()
    defaults["temp_dir"] = Path(defaults["temp_dir"]).resolve()

    # CD to the working directory
    working_dir = kwargs.directory or defaults["directory"]
    os.chdir(working_dir)

    # Load config file options (setup.cfg)
    res = config_file()

    #  If outdir was specified in the config file, then it is relative to the config file
    if "outdir" in res:
        res["outdir"] = Path(res["outdir"]).resolve()
    if "temp_dir" in res:
        res["temp_dir"] = Path(res["temp_dir"]).resolve()

    # Apply defaults as specified in args.yml
    for k, v in defaults.items():
        if k not in res:
            res[k] = v

    # Override config and defaults with cli args
    res.update({k: v for k, v in kwargs.__dict__.items() if v is not None})
    res["outdir"].mkdir(exist_ok=True)

    return res
