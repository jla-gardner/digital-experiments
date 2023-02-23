from datetime import datetime
from typing import Any, Callable, Dict, Tuple

from . import control_center as GLOBAL


def now():
    """
    get the current timestamp
    """
    return datetime.now().timestamp()


def record_metadata(
    func: Callable, args: Tuple, kwargs: Dict
) -> Tuple[Dict, Any]:
    """
    record metadata for a function's execution
    """

    start = now()
    result = func(*args, **kwargs)
    end = now()
    metadata = {"time": {"start": start, "end": end, "duration": end - start}}
    metadata.update(GLOBAL.current_metadata())
    return metadata, result
