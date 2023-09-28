import os
import shutil
import subprocess
from pathlib import Path

DRY_RUN = False
log = Path("commands").absolute()


def call(cmd, **kw):
    with log.open(mode="a") as f:
        f.write(" ".join([str(x) for x in cmd]) + "\n")
    if not DRY_RUN:
        subprocess.call(cmd, **kw)


def copy(src, dst, **kw):
    with log.open(mode="a") as f:
        f.write(f"copy {src} {dst}\n")
    if not DRY_RUN:
        shutil.copyfile(src=str(src), dst=str(dst), **kw)


def copytree(src, dst, **kw):
    with log.open(mode="a") as f:
        f.write(f"copy -r {src} {dst}\n")
    if not DRY_RUN:
        shutil.copytree(src=str(src), dst=str(dst), **kw)


def move(src, dst, **kw):
    with log.open(mode="a") as f:
        f.write(f"move {src} {dst}\n")
    if not DRY_RUN:
        shutil.move(src=str(src), dst=str(dst), **kw)


def cd(dir):
    with log.open(mode="a") as f:
        f.write(f"cd {dir}\n")
    os.chdir(str(dir))
