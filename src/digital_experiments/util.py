from datetime import datetime


def generate_id():
    return datetime.now().strftime("%y.%m.%d-%H.%M.%S-%f")
