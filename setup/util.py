import os
import datetime

import importlib.machinery
# ============================================================================

#TODO rename resolve_path_absolute
def resolve_abs_path(path):
    return os.path.abspath(os.path.expanduser(path))


def resolve_path(path):
    return os.path.join(*(path.split("/")))


def get_absolute_dirname(path):
        directory_name = os.path.dirname(path)
        return resolve_abs_path(directory_name)


def time_stamped(fname, fmt="{fname}_%Y-%m-%d-%H-%M-%S"):
    return datetime.datetime.now().strftime(fmt).format(fname=fname)


def dynamic_import(path, module_name):
    # TODO add option to override this path with a custom one
    # TODO add compatibility for python 3.3 through 3.5
    # http://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path
    setup_config_location = resolve_abs_path(path)
    loader = importlib.machinery.SourceFileLoader(module_name, setup_config_location)
    return loader.load_module()
