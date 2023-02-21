import inspect


def complete_config(func, args, kwargs) -> dict:
    """
    get the complete config (including defaults) for a function
    """

    signature = inspect.signature(func)
    config = signature.bind(*args, **kwargs)
    config.apply_defaults()
    return dict(**config.arguments)


def code_for(func):
    """
    get the code for a function
    """

    return inspect.getsource(func)
