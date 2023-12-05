from digital_experiments.util import complete_config, source_code


def my_func(a):
    return a + 1


def test_get_code():
    code = source_code(my_func)
    assert code == "def my_func(a):\n    return a + 1\n"


def test_complete_config():
    def my_func(a, b=1):
        return a + b

    config = complete_config(my_func, (1,), {})
    assert config == {"a": 1, "b": 1}
