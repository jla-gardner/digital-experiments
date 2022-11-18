from digital_experiments.tee import stdout_to_


def test_stdout_to_(tmpdir):
    file = tmpdir / "test.txt"
    with stdout_to_(file) as f:
        print("hello")
        print("world")
    
    assert file.read() == "hello\nworld\n"


