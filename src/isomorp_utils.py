import os
import sys


def is_micropython():
    # type: () -> bool
    return sys.implementation.name is 'micropython'


def path_join(*paths):
    # type: (*str) -> str
    if is_micropython():
        return os.sep.join([p.strip('/') for p in paths])
    else:
        return os.path.join(*paths)


def file_size(path):
    # type: (str) -> int
    if is_micropython():
        return os.stat(path)[6]
    else:
        return os.stat(path).st_size
