
from pathlib import Path
from .parse_args import config
from .utils.settings import ConstructorSettings, ElectronSettings

CONFIG = config()

CONSTRUCTOR_PARAMS = ConstructorSettings(**CONFIG)

ELECTRON_PARAMS = ElectronSettings(CONFIG)
