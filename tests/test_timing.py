from digital_experiments import experiment, timing


def test_timing(tmp_path):
    @experiment(root=tmp_path)
    def my_experiment():
        a = sum(range(100))
        timing.mark("sum")

        with timing.time_block("sum"):
            b = sum(range(1000))

        return a + b

    my_experiment()
    observation = my_experiment.observations[-1]

    marks = observation.metadata["timing_marks"]
    assert len(marks) == 3
    assert "start sum end".split() == [name for name, _ in marks]
    assert marks[0][1] < marks[1][1] < marks[2][1]

    print(observation.metadata)
    blocks = observation.metadata["timing"]
    assert len(blocks) == 1
    assert "sum" in blocks
