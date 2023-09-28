import os
import shutil
import subprocess
from pathlib import Path
import zipfile

SETTINGS = dict(DRY_RUN = False, log = Path("commands").absolute())


def call(cmd, **kw):
    with SETTINGS["log"].open(mode="a") as f:
        f.write(" ".join([str(x) for x in cmd]) + "\n")
    if not SETTINGS["DRY_RUN"]:
        subprocess.call(cmd, **kw)


def copy(src, dst, **kw):
    with SETTINGS["log"].open(mode="a") as f:
        f.write(f"cp {src} {dst}\n")
    if not SETTINGS["DRY_RUN"]:
        shutil.copyfile(src=str(src), dst=str(dst), **kw)


def copytree(src, dst, **kw):
    with SETTINGS["log"].open(mode="a") as f:
        f.write(f"cp -r {src} {dst}\n")
    if not SETTINGS["DRY_RUN"]:
        shutil.copytree(src=str(src), dst=str(dst), **kw)


def move(src, dst, **kw):
    with SETTINGS["log"].open(mode="a") as f:
        f.write(f"mv {src} {dst}\n")
    if not SETTINGS["DRY_RUN"]:
        shutil.move(src=str(src), dst=str(dst), **kw)


def cd(dir):
    with SETTINGS["log"].open(mode="a") as f:
        f.write(f"cd {dir}\n")
    if not SETTINGS["DRY_RUN"]:
        os.chdir(str(dir))

def zipdir(src, dst):
    with SETTINGS["log"].open(mode="a") as f:
        f.write(f"zip {src} {dst}\n")
    if not SETTINGS["DRY_RUN"]:
        with zipfile.ZipFile(
            dst, "w", zipfile.ZIP_DEFLATED
        ) as ziph:
            # ziph is zipfile handle
            for root, dirs, files in os.walk(src):
                for file in files:
                    ziph.write(
                        os.path.join(root, file),
                        os.path.relpath(os.path.join(root, file), os.path.join(src, "..")),
                    )
