from src.log import setup_logger
from src.constants.paths.log import DASH_LOG

logger = setup_logger(__name__, DASH_LOG, add_console=False)