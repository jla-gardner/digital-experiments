from datetime import datetime


def now():
    """
    get the current timestamp
    """
    return datetime.now().timestamp()


def record_metadata(func, args, kwargs) -> tuple:
    """
    record metadata for a function's execution
    """

    start = now()
    result = func(*args, **kwargs)
    end = now()
    metadata = {"time": {"start": start, "end": end, "duration": end - start}}
    return metadata, result
