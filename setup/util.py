import os
import datetime

# ============================================================================

def resolve_abs_path(path):
    return os.path.abspath(os.path.expanduser(path))


def resolve_path(path):
    return os.path.join(*(path.split("/")))


def time_stamped(fname, fmt="{fname}_%Y-%m-%d-%H-%M-%S"):
    return datetime.datetime.now().strftime(fmt).format(fname=fname)
