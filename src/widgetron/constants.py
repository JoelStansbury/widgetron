import platform
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).parent
PYTHON = Path(sys.executable)
CONDA_PREFIX = PYTHON.parent
TEMP_DIR = Path("widgetron_temp_files").absolute()
DEFAULT_BLD = TEMP_DIR / "conda_bld"
DEFAULT_SERVER_COMMAND = ["jupyter", "lab", "--no-browser"]

NPM = shutil.which("npm")
CONDA = shutil.which("mamba") or shutil.which("conda")
JAKE = shutil.which("jake")
CONSTRUCTOR = shutil.which("constructor")

WIN = platform.system() == "Windows"
LINUX = platform.system() == "Linux"
OSX = platform.system() == "Darwin"

REQUIRED_PKGS = [
    ("jupyterlab", ">=3"),
    ("conda", ">=22, <23"),
    *([("menuinst", ">=1.4.17")] if WIN else []),
]

if WIN:
    DEFAULT_ICON = (HERE / "icons/widgetron.ico").absolute()
elif LINUX:
    DEFAULT_ICON = (HERE / "icons/widgetron.png").absolute()
elif OSX:
    DEFAULT_ICON = (HERE / "icons/widgetron.icns").absolute()
else:
    raise OSError(f"Unknown platform {platform.system()}")
