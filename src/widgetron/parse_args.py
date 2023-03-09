import argparse
import os
from pathlib import Path

import configparser
import toml
import yaml

HERE = Path(__file__).parent
ARGS_FILE = HERE / "args.yml"


parser = argparse.ArgumentParser(
    prog="widgetron",
    description="Creates an app for displaying the output cells of an interactive notebook.",
)

def defaults():
    if Path("setup.cfg").is_file():
        setup_cfg = configparser.ConfigParser()
        with Path("setup.cfg").open("r") as f:
            setup_cfg.read_file(f)
        if "tool.widgetron" in setup_cfg:
            print("Initialize from setup.cfg")
            return setup_cfg._sections["tool.widgetron"]
    
    if Path("pyproject.toml").is_file():
        _toml = toml.load(Path("pyproject.toml"))
        if "tool" in _toml:
            if "widgetron" in _toml["tool"]:
                print("Initialize from pyproject.toml")
                return _toml["tool"]["widgetron"]
    return {}

def config():
    with ARGS_FILE.open() as f:
        args = yaml.safe_load(f)
    for k, v in args.items():
        flags = [v.pop("flag"), "--"+k]
        parser.add_argument(*flags, **v)
    kwargs = parser.parse_args()
    os.chdir(kwargs.directory)
    res = defaults()
    res.update({k:v for k,v in kwargs.__dict__.items() if v is not None})
    return res

CONFIG = config()

if __name__ == "__main__":
    print(CONFIG)