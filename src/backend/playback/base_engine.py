from logging import Logger
from typing import Callable
from abc import ABC, abstractmethod

from src.sentinels import Sentinel
from src.config import CONFIG

class BaseEngine(ABC):
    def __init__(self, logger: Logger, name: str, on_end_func: Callable):
        self.logger = logger
        self.name = name
        self.on_end = on_end_func
        self.medias: list = []
        self.number: int = 0
        self.volume: int = CONFIG.default_volume
        self.mute: bool = False

    @abstractmethod
    def get_status(self) -> Sentinel:
        ...

    @abstractmethod
    def get_progress(self) -> tuple[int, int]: # (time, length)
        ...

    @abstractmethod
    def load_number(self) -> Sentinel:
        ...

    @abstractmethod
    def load_paths(self, paths: list[str]) -> Sentinel:
        ...

    @abstractmethod
    def stop(self) -> Sentinel:
        ...

    @abstractmethod
    def jump_pos(self, pos: int) -> Sentinel:
        ...

    @abstractmethod
    def play(self) -> Sentinel:
        ...

    @abstractmethod
    def pause(self) -> Sentinel:
        ...

    @abstractmethod
    def resume(self) -> Sentinel:
        ...

    @abstractmethod
    def apply_volume(self) -> Sentinel:
        ...
    
    @abstractmethod
    def on_exit(self) -> Sentinel:
        ...
