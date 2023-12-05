import inspect
from typing import Any, Callable, Dict


def complete_config(func, args, kwargs) -> Dict[str, Any]:
    """get the complete config (including defaults) for a function"""

    signature = inspect.signature(func)
    config = signature.bind(*args, **kwargs)
    config.apply_defaults()
    return dict(**config.arguments)


def source_code(function: Callable) -> str:
    """get the source code for `function`"""

    return inspect.getsource(function)
