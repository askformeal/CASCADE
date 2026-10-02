import subprocess
import sys
import os
from time import sleep
from pathlib import Path

import psutil

from src.frontend.client import test_alive, send_request
from src.constants.process import (
    STARTER_RETRY, 
    STARTER_CHECK_INTERVAL, 
    TERMINATE_TIMEOUT, 
    RESTART_NUM, 
    RESTART_POLL_INTERVAL
    )
from src.config import CONFIG
from src.sentinels import SENTINELS
from src.pid import get_pid, remove_pid

class ProcessManager:
    def __init__(self, logger):
        self.logger = logger

    def start(self, **kwargs):
        self.logger.info(f'Starting backend, environment variables: {kwargs}...')
        if test_alive():
            self.logger.warning('Backend already running')
            return SENTINELS.BACKEND_ALREADY_RUNNING
        else:
            self.spawn('src.backend.core', **kwargs)
            if CONFIG.hotkey:
                self.spawn('src.frontend.hotkey')
            if CONFIG.tray:
                self.spawn('src.frontend.tray')
            if CONFIG.lyric:
                self.spawn('src.frontend.lyric')
                
            for i in range(STARTER_RETRY):
                if test_alive():
                    self.logger.info('Backend started')
                    return SENTINELS.SUCCESS
                sleep(STARTER_CHECK_INTERVAL)

            self.logger.info('Timed out waiting backend to be alive')
            return SENTINELS.FAILED_START_BACKEND

    def reboot(self, **kwargs):
        self.logger.info('Rebooting backend...')
        if not test_alive():
            self.logger.warning('Backend not running')
            return SENTINELS.BACKEND_NOT_RUNNING
        else:
            response = send_request(action='exit', source='process', notify_support=False)
            if response.get('code', None) != 0:
                self.logger.warning(f'Failed to exit - unsuccessful response: {response}')
                return SENTINELS.FAILED_EXIT_BACKEND
            else:
                for i in range(RESTART_NUM):
                    sleep(RESTART_POLL_INTERVAL)
                    if not test_alive():
                        break
                else:
                    self.logger.warning(f'Failed to exit - timed out waiting for backend to be dead')
                    return SENTINELS.FAILED_EXIT_BACKEND
                    
                return self.start(**kwargs)

    def spawn(self, module, **env_args):
        self.logger.info(f'Spawn module {module} with environment arguments {env_args}')
        for key, value in env_args.items():
            env_args[key] = str(value)
        env = {**os.environ, **env_args}

        if sys.platform == 'win32':
            pythonw = sys.executable.replace('python.exe', 'pythonw.exe')
            if Path(pythonw).exists():
                exe = pythonw
                flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                exe = sys.executable
                flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
            subprocess.Popen([exe, '-m', module], env=env, 
                                creationflags=flags,
                                stdin=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                                )
        else:
            args = [sys.executable, '-m', module]
            subprocess.Popen(args, env=env, 
                                start_new_session=True,
                                stdin=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                                )

    def kill(self):
        pids = get_pid()
        result = []

        for pid in pids:
            try:
                pid = int(pid)
            except ValueError:
                result.append((pid, SENTINELS.INVALID_PID))
            else:
                try:
                    process = psutil.Process(pid)
                except psutil.NoSuchProcess:
                    result.append((pid, SENTINELS.PROCESS_NOT_FOUND))
                except psutil.AccessDenied:
                    result.append((pid, SENTINELS.PERMISSION_INSUFFICIENT))
                else:
                    process.terminate()
                    try:
                        process.wait(timeout=TERMINATE_TIMEOUT)
                    except psutil.TimeoutExpired:
                        process.kill()
                        remove_pid(pid)
                        result.append((pid, SENTINELS.FORCE_KILL))
                    else:
                        remove_pid(pid)
                        result.append((pid, SENTINELS.GRACE_KILL))

        return result