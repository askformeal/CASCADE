from src import gen_response
from src.gen_response import Response
from src.backend.context import Context

def test_alive(ctx: Context, request: dict) -> Response:
    return gen_response.Success('CASCADE backend is running')

def get_notifies(ctx: Context, request: dict) -> Response:
    return gen_response.Success('notifies obtained')

def exit_(ctx: Context, request: dict) -> Response:
    ctx.exit_()
    return gen_response.Success('CASCADE backend is now exiting')