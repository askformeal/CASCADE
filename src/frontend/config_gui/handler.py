from tkinter import messagebox

from .logger import logger
from src.config_manager import CONFIG_MANAGER
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .core import ConfigGUI

class HandlerMixin:
    def set_value(self: 'ConfigGUI', name: str, value, overwrite_corrupt: bool = False):
        logger.info(f'Set \"{name}\" to \"{value}\", overwrite corrupted: {overwrite_corrupt}')
        if self.remote:
            response = self._send_config_request(
                'config.set', 
                option=name, 
                value=value,
                overwrite_corrupt=overwrite_corrupt
                )
        else:
            response = dict(CONFIG_MANAGER.set_option_value(
                name=name,
                value=value,
                overwrite_corrupt=overwrite_corrupt
            ))
    
        self._handle_response(response)
    
    def unset(self: 'ConfigGUI', name: str):
        logger.info(f'Unset: {name}')
        if self.remote:
            response = self._send_config_request('config.unset', option=name)
        else:
            response = CONFIG_MANAGER.unset_option(name)
        self._handle_response(response)

    def open_file(self: 'ConfigGUI'):
        logger.info(f'Open config file')
        if self.remote:
            response = self._send_config_request('config.open')
        else:
            response = dict(CONFIG_MANAGER.open_config_file())

        self._handle_response(response, update=False)

    def copy_path(self: 'ConfigGUI', *_):
        logger.info(f'Copy config file path')
        if self.remote:
            response = self._send_config_request('config.path')
        else:
            response = dict(CONFIG_MANAGER.get_path())

        if self._handle_response(response, update=False):
            path = response['attachment']
            self.clipboard_clear()
            self.clipboard_append(path)
            logger.info(f'Copied to clipboard: {path}')
            self.after(0, lambda: messagebox.showinfo(
                title='Path copied', 
                message=f'Copied to clipboard',
                detail=path
                ))

    def _handle_response(self: 'ConfigGUI', response: dict, update: bool = True) -> bool:
        logger.info(f'Handle response: {response}')
        if response['code'] == 0:
            if update:
                self._update_options()
            return True
        else:
            msg = response['msg']
            self.after(0, lambda: messagebox.showerror(
                title='Failed',
                message='Unsuccessful response',
                detail=msg
                ))
            return False