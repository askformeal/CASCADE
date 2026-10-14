from dataclasses import dataclass
from typing import Callable

from .database.core import Database
from .playback.core import Playback
from .task import TaskManager

@dataclass
class Context:
    database: Database
    playback: Playback
    task: TaskManager
    exit_: Callable
    start_time: int
    dev: bool
    notify: Callable
    get_request_rate: Callable
