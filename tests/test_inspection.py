from digital_experiments.inspection import code_for, complete_config


def test_get_code():
    def my_func(a):
        return a + 1

    code = code_for(my_func)
    assert code == "    def my_func(a):\n        return a + 1\n"


def test_complete_config():
    def my_func(a, b=1):
        return a + b

    config = complete_config(my_func, (1,), {})
    assert config == {"a": 1, "b": 1}
