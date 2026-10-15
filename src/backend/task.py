import time
from copy import deepcopy

from src.sentinels import SENTINELS

class Task:
    def __init__(self, max_progress: int = 0, name: str = ''):
        self.status = SENTINELS.TASK_RUNNING
        self.progress = 0
        self.max_progress = max_progress
        self.name = name
        self.logs = []

class TaskManager:
    def __init__(self):
        self.tasks: list[Task] = []

    def list_(self) -> list[dict]:
        result = []
        for task in self.tasks:
            result.append({
                'name': task.name,
                'status': task.status,
                'progress': task.progress,
                'max_progress': task.max_progress,
                'logs': task.logs
            })
        return deepcopy(result)

    def add_task(self, max_progress: int = 0, name: str = '') -> int:
        task = Task(max_progress=max_progress, name=name)
        self.tasks.append(task)
        index = self.tasks.index(task)
        self.log_task(index, 'Task start')
        return index

    def task_succeeded(self, index: int, record: str | None = None):
        if record is not None:
            self.log_task(index, record)
        self.tasks[index].status = SENTINELS.TASK_SUCCEEDED

    def task_failed(self, index: int, record: str | None = None):
        if record is not None:
            self.log_task(index, record)
        self.tasks[index].status = SENTINELS.TASK_FAILED

    def set_task_progress(self, index: int, progress: int):
        self.tasks[index].progress = progress

    def nudge_task_progress(self, index: int, step: int = 1):
        self.tasks[index].progress += step

    def log_task(self, index: int, record: str):
        self.tasks[index].logs.append([time.time(), record])
