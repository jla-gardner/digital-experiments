def pad(thing, pad=" "):
    """
    pad an optionally multi-line string
    """

    return "\n".join([pad + line for line in thing.splitlines()])


def pretty_instance(class_name, *things, **keywords) -> str:
    """
    make a pretty representation of an instance of a class
    """

    all_things = list(map(str, things)) + [
        f"{k}={v}" for k, v in keywords.items()
    ]

    naive_rep = f"{class_name}({', '.join(all_things)})"
    if len(naive_rep) < 80:
        return naive_rep

    # if the naive representation is too long, we try to make it more readable
    # by putting each argument on a new line
    padded_things = "\n".join(pad(thing) for thing in all_things)
    return f"{class_name}(\n{padded_things}\n)"
