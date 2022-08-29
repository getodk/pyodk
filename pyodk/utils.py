STRPTIME_FMT_UTC = "%Y-%m-%dT%H:%M:%S.%fZ"


def coalesce(*args):
    return next((a for a in args if a is not None), None)
