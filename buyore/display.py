
__all__ = (
    'action',
    'title',
    )

import sys
import time

TITLE = b'32'
CMDLINE = b'34'
RESET = b'\033[0m'

verbosity = 0
colorize = True

def cprint(color, *args, **kw):
    if not verbosity:
        return
    if colorize:
        ff = kw.get('file', sys.stdout).buffer
        ff.write(b'\033[' + color + b'm')
    print(*args, **kw)
    if colorize:
        ff.write(RESET)
        ff.flush()

def title(value):
    if verbosity:
        cprint(TITLE, '==>', value)

def commandline(cmdline):
    if verbosity >= 2:
        cprint(CMDLINE, '  !', *cmdline)

class action(object):

    def __init__(self, title):
        self.title = title
        self._inside = False
        self._time = None

    def __enter__(self):
        if self._time:
            raise RuntimeError("Can't enter same action twice")
        cprint(TITLE, '==>', self.title, end=' ... ')
        self._time = time.time()
        return self

    def __exit__(self, exc_type, exc_value, ext_tb):
        d = time.time() - self._time
        cprint(TITLE, ' ... done in {:.2f}s'.format(d))

    def add(self, text):
        if not self._time:
            raise RuntimeError("Bad time for adding info")
        cprint(TITLE, text, end=' ')
