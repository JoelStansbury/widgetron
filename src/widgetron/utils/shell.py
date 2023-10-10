import os
import shutil
import subprocess
from pathlib import Path
import zipfile


class Shell:
    def __init__(self, mock=False, log=None):
        self.log = log or Path("shell_commands.txt")
        self.mock = mock

    def _log(self, msg):
        with self.log.open(mode="a") as f:
            f.write(msg)

    def call(self, cmd, **kw) -> int:
        self._log(" ".join([str(x) for x in cmd]) + "\n")
        for k, v in kw.items():
            self._log(f"  {k}: {v}\n")
        if not self.mock:
            return subprocess.call(cmd, **kw)
        return 0

    def check_output(self, cmd, **kw) -> str:
        self._log(" ".join([str(x) for x in cmd]) + "\n")
        for k, v in kw.items():
            self._log(f"  {k}: {v}\n")
        if not self.mock:
            return subprocess.check_output(cmd, **kw)
        return ""

    def copy(self, src, dst, **kw):
        self._log(f"cp {src} {dst}\n")
        for k, v in kw.items():
            self._log(f"  {k}: {v}\n")
        if not self.mock:
            shutil.copyfile(src=str(src), dst=str(dst), **kw)

    def copytree(self, src, dst, **kw):
        self._log(f"cp -r {src} {dst}\n")
        for k, v in kw.items():
            self._log(f"  {k}: {v}\n")
        if not self.mock:
            shutil.copytree(src=str(src), dst=str(dst), **kw)

    def move(self, src, dst, **kw):
        self._log(f"mv {src} {dst}\n")
        for k, v in kw.items():
            self._log(f"  {k}: {v}\n")
        if not self.mock:
            shutil.move(src=str(src), dst=str(dst), **kw)

    def cd(self, dir):
        self._log(f"cd {dir}\n")
        if not self.mock:
            os.chdir(str(dir))

    def zipdir(self, src, dst):
        self._log(f"zip {src} {dst}\n")
        if not self.mock:
            with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as ziph:
                # ziph is zipfile handle
                for root, dirs, files in os.walk(src):
                    for file in files:
                        ziph.write(
                            os.path.join(root, file),
                            os.path.relpath(
                                os.path.join(root, file), os.path.join(src, "..")
                            ),
                        )


SHELL = Shell()
