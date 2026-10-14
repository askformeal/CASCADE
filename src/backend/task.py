from src.sentinels import SENTINELS

class Task:
    def __init__(self, max_progress: int = 0, msg: str = ''):
        self.status = SENTINELS.TASK_RUNNING
        self.progress = 0
        self.max_progress = max_progress
        self.msg = msg

class TaskManager:
    def __init__(self):
        self.tasks: list[Task] = []

    def list_(self) -> list[dict]:
        result = []
        for task in self.tasks:
            result.append({
                'status': task.status,
                'progress': task.progress,
                'max_progress': task.max_progress,
                'msg': task.msg
            })
        return result

    def add_task(self, max_progress: int = 0, msg: str = '') -> int:
        task = Task(max_progress=max_progress, msg=msg)
        self.tasks.append(task)
        return self.tasks.index(task)

    def task_complete(self, index: int):
        self.tasks[index].status = SENTINELS.TASK_SUCCEED

    def task_failed(self, index: int):
        self.tasks[index].status = SENTINELS.TASK_FAILED

    def set_task_progress(self, index: int, progress: int):
        self.tasks[index].progress = progress
