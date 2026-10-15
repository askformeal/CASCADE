from src.sentinels import SENTINELS
from src import gen_response
from src.gen_response import Response
from src.backend.context import Context

def get_tasks(ctx: Context, request: dict) -> Response:
    status = {
        SENTINELS.TASK_RUNNING: 'running',
        SENTINELS.TASK_SUCCEEDED: 'succeeded',
        SENTINELS.TASK_FAILED: 'failed'
    }
    tasks = ctx.task.list_()
    for i, task in enumerate(tasks):
        tasks[i]['status'] = status[task['status']]

    return gen_response.Success('tasks obtained', attachment=tasks)
