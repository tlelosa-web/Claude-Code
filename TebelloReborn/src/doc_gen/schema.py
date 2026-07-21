from enum import Enum


class GenerationStatus(Enum):
    SUCCESS = "success"
    THROTTLED = "throttled"
    ERROR = "error"
