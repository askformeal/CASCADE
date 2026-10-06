import time
from tkinter import messagebox
from threading import Thread

from .logger import logger
from src.frontend.client import test_heartbeat
from src.constants.frontend import HEARTBEAT_POLL_INTERVAL
from src.sentinels import SENTINELS
from src.process import ProcessManager

class LifecycleMixin:
    def __init__(self):
        self.process = ProcessManager(logger)

    def check_backend(self):
        def check():
            response = self._send_gui_request(action='test_alive')
            code = response['code']
            msg = f'Received response with code {code}'
            detail = response['msg']
            if code == 0:
                self.after(0, lambda: messagebox.showinfo(title='Backend online', message=msg, detail=detail))
            else:
                self.after(0, lambda: messagebox.showerror(title='Connection failed', message=msg, detail=detail))
        Thread(target=check).start()

    def start_backend(self, continue_=False, dev=False):
        def start(continue_, dev):
            continue_ = str(int(continue_))
            dev = str(int(dev))
            result = self.process.start(CASCADE_CONTINUE=continue_, CASCADE_DEV=dev)
            if result is SENTINELS.SUCCESS:
                self.after(0, lambda: messagebox.showinfo( 
                        title='Backend started', 
                        message='Backend is now up and running'
                        ))
            elif result is SENTINELS.BACKEND_ALREADY_RUNNING:
                self.after(0, lambda: messagebox.showinfo( 
                        title='Backend already running', 
                        message='Backend is already running'
                        ))
            elif result is SENTINELS.FAILED_START_BACKEND:
                self.after(0, lambda: messagebox.showinfo(
                        title='Error', 
                        message='Failed to start backend',
                        detail='Timed out waiting for backend to be alive'
                        ))
        Thread(target=start, args=(continue_, dev)).start()

    def reboot_backend(self, continue_=False, dev=False):
        def reboot(continue_, dev):
            continue_ = str(int(continue_))
            dev = str(int(dev))
            result = self.process.reboot(CASCADE_CONTINUE=continue_, CASCADE_DEV=dev)
            if result is SENTINELS.SUCCESS:
                self.after(0, lambda: messagebox.showinfo(
                        title='Backend rebooted', 
                        message='Backend is shutdown and restarted'
                        ))
            elif result is SENTINELS.BACKEND_NOT_RUNNING:
                self.after(0, lambda: messagebox.showinfo(
                        title='Error', 
                        message='Backend is not running',
                        ))
            elif result is SENTINELS.FAILED_EXIT_BACKEND:
                self.after(0, lambda: messagebox.showinfo(
                        title='Error', 
                        message='Failed to exit backend',
                        ))
            elif result is SENTINELS.FAILED_START_BACKEND:
                self.after(0, lambda: messagebox.showinfo(
                        title='Error', 
                        message='Failed to start backend',
                        detail='Backend is shutdown but failed to be restarted'
                        ))
        Thread(target=reboot, args=(continue_, dev)).start()

    def monitor_heartbeat(self):
        while self.running:
            time.sleep(HEARTBEAT_POLL_INTERVAL)

            code = test_heartbeat()
            if code == 0:
                self.backend_online = True
            else:
                self.backend_online = False