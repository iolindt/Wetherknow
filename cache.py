cached = None


def save(weather):

    global cached

    cached = weather


def load():

    return cached
