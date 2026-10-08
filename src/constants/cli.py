from src import __version__
from .misc import REPO_LINK
from src.utils.escape_code import ESCAPE_CODE as EC

FAIL_TAG = f'{EC.bold}{EC.red}[Failed]{EC.rs}:'
OK_TAG = f'{EC.bold}{EC.green}[Succeeded]{EC.rs}:'

NON_REQUEST_KEYS = ('verbose', 'dev', 'yes', 'direct')

HELP_DESCRIPTION = f'''
Command-line Audio Stream Capture And Decoding Engine

Version: {__version__}
Author: Edward (muzhi1014@outlook.com)

GitHub Repository: {REPO_LINK}

Use cascade start to start backend.
Use cascade gui to open GUI app.

Check out README for more information.

Have fun!
'''
