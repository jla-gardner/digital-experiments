@experiment(backend="csv")
def modified_himmelbau(x, y):
    himmelbau = (x ** 2 + y - 11) ** 2 + (x + y ** 2 - 7) ** 2
    return himmelbau + 0.5 * x + y + 20
