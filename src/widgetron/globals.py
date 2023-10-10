from .parse_args import config
from .utils.settings import ConstructorSettings

CONFIG = config()

CONSTRUCTOR_PARAMS = ConstructorSettings(**CONFIG)
