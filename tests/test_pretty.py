from digital_experiments.pretty import pretty_instance


def test_pretty():
    rep = pretty_instance("MyClass", "hello", a=True)
    assert rep == "MyClass(hello, a=True)"

    # if the naive representation is too long, we try to make it more readable
    # by putting each argument on a new line
    rep = pretty_instance(
        "MyClass",
        "a really really really really really long string",
        some="other",
        args="here",
    )
    print(rep)

    assert (
        rep
        == """MyClass(
    a really really really really really long string,
    some=other,
    args=here,
)"""
    )
