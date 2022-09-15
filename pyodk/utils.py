def coalesce(*args):
    return next((a for a in args if a is not None), None)
