from src.log import setup_logger
from src.constants.paths.log import BACKEND_LOG
from src.config_manager import CONFIG_MANAGER
from src.gen_response import Response
from src.backend.context import Context

logger = setup_logger(__name__, BACKEND_LOG)

def list_(ctx: Context, request: dict) -> Response:
    return CONFIG_MANAGER.get_all_option_info()

def show(ctx: Context, request: dict) -> Response:
    option = request['option']
    return CONFIG_MANAGER.get_option_info(option)

def set_(ctx: Context, request: dict) -> Response:
    option = request['option']
    value = request['value']
    overwrite_corrupt = request['overwrite_corrupt']
    return CONFIG_MANAGER.set_option_value(option, value, overwrite_corrupt=overwrite_corrupt)

def unset(ctx: Context, request: dict) -> Response:
    option = request['option']
    return CONFIG_MANAGER.unset_option(option)

def open_(ctx: Context, request: dict) -> Response:
    return CONFIG_MANAGER.open_config_file()

def path(ctx: Context, request: dict) -> Response:
    return CONFIG_MANAGER.get_path()