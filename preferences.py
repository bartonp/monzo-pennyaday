import os
import sys
import contextlib

try:
    _ = WindowsError
except NameError:
    class WindowsError(Exception):
        pass


@contextlib.contextmanager
def suppress(*exceptions):
    try:
        yield
    except exceptions:
        pass


def get_config_dir(company=None, app=None):
    p = None
    if sys.platform == 'win32':
        p = os.path.expandvars(os.path.join('%APPDATA%', company, app))
    elif sys.platform == 'darwin':
        p = os.path.expanduser(os.path.join('~', 'Library', 'Application Support', company, app))
    elif sys.platform == 'linux2':
        p = os.path.expanduser(os.path.join('~', '.config', company, app))

    if p is not None and __name__ is not '__main__':
        with suppress(OSError, WindowsError):
            os.makedirs(p)

    return p

__all__ = ['get_config_dir']