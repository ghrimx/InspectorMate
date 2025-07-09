from functools import wraps
from PyQt6.QtCore import QObject, pyqtSignal as Signal

def singleton(cls):
    """Make a class a Singleton class (only one instance)"""
    @wraps(cls)
    def wrapper_singleton(*args, **kwargs):
        if wrapper_singleton.instance is None:
            wrapper_singleton.instance = cls(*args, **kwargs)
        return wrapper_singleton.instance
    wrapper_singleton.instance = None
    return wrapper_singleton

class StatusSignal(QObject):
    status_message = Signal(str, int)

status_signal = StatusSignal()

def status_message(message: str, time: int = 5000):
    """
    Decorator that emits a status message before calling the wrapped function.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            status_signal.status_message.emit(message, time)
            return func(*args, **kwargs)
        return wrapper
    return decorator