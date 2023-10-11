from pathlib import Path
from .parse_args import config
from .utils.settings import ConstructorSettings

CONFIG = config()

CONSTRUCTOR_PARAMS = ConstructorSettings(
    path=Path(CONFIG["temp_dir"]).resolve() / "constructor",
    **CONFIG
)
