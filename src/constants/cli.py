from src.utils.escape_code import ESCAPE_CODE as EC

FAIL_TAG = f'{EC.bold}{EC.red}[Failed]{EC.rs}:'
OK_TAG = f'{EC.bold}{EC.green}[Succeeded]{EC.rs}:'

NON_REQUEST_KEYS = ('verbose', 'dev', 'yes', 'direct')

HELP_DESCRIPTION = '''
Command-line Audio Stream Capture And Decoding Engine

Author: Edward

'''
