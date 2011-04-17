
__all__ = (
    'action',
    )

import sys
import time

TITLE = b'32'
RESET = b'\033[0m'

def cprint(color, *args, **kw):
    ff = kw.get('file', sys.stdout).buffer
    ff.write(b'\033[' + color + b'm')
    print(*args, **kw)
    ff.write(RESET)

class action(object):

    def __init__(self, title):
        self.title = title
        self._inside = False
        self._time = None

    def __enter__(self):
        if self._time:
            raise RuntimeError("Can't enter same action twice")
        cprint(TITLE, '==> ' + self.title, end=' ... ')
        self._time = time.time()
        return self

    def __exit__(self, exc_type, exc_value, ext_tb):
        d = time.time() - self._time
        cprint(TITLE, ' ... done in {:.2f}s'.format(d))

    def add(self, text):
        if not self._time:
            raise RuntimeError("Bad time for adding info")
        cprint(TITLE, text, end=' ')
