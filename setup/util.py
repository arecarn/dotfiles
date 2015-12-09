import os
import datetime

import importlib.machinery
# ============================================================================

def resolve_abs_path(path):
    return os.path.abspath(os.path.expanduser(path))


def resolve_path(path):
    return os.path.join(*(path.split("/")))


def time_stamped(fname, fmt="{fname}_%Y-%m-%d-%H-%M-%S"):
    return datetime.datetime.now().strftime(fmt).format(fname=fname)


def dynamic_import(path, module_name):
    # TODO add option to override this path with a custom one
    # TODO add compatibility for python 3.3 through 3.5
    # http://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path
    setup_config_location = resolve_abs_path("~/dotfiles/setup_config.py")
    loader = importlib.machinery.SourceFileLoader('setup_config', setup_config_location)
    return loader.load_module()
