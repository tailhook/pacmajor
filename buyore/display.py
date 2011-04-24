
__all__ = (
    'action',
    'title',
    )

import sys
import tty
import time

TITLE = b'32'
CMDLINE = b'34'
RESET = b'\033[0m'
LETTERS = 'abcdefghijklmnoprstuvwxyz'

verbosity = 0
colorize = True

FILE_NEW = 0
FILE_VIEWED = 1
FILE_MODIFIED = 2
modes = {
    FILE_NEW: '\033[34m[ ]',
    FILE_MODIFIED: '\033[34m[*]',
    FILE_VIEWED: '\033[34m[+]',
    }

class CommandExecute(Exception):

    def __init__(self, name, arg=None):
        self.name = name
        self.arg = arg

def letterify(iter):
    return zip(LETTERS, iter)

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

def pkgfile(mode, pkgname, fn):
    if fn == 'PKGBUILD':
        return modes[mode]+' \033[37m' + pkgname + '\033[34m/' + fn + '\033[0m'
    else:
        return modes[mode]+' '+' '*len(pkgname) + ' \033[34m' + fn + '\033[0m'

def title(value):
    if verbosity:
        cprint(TITLE, '==>', value)

def commandline(cmdline):
    if verbosity >= 2:
        cprint(CMDLINE, '  !', *cmdline)
def print_item(*a, **kw):
    print('   ', *a, **kw)

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

class section(object):

    def __init__(self, title):
        self.title = title
        self._inside = False
        self._time = None

    def __enter__(self):
        if self._time:
            raise RuntimeError("Can't enter same action twice")
        cprint(TITLE, '==>', self.title, end=' ...\n')
        self._time = time.time()
        return self

    def __exit__(self, exc_type, exc_value, ext_tb):
        d = time.time() - self._time
        cprint(TITLE, '--> done in {:.2f}s'.format(d))

    def add(self, text):
        if not self._time:
            raise RuntimeError("Bad time for adding info")
        cprint(TITLE, '   ', text)

def menu(title, names, **cmds):
    attr = tty.tcgetattr(sys.stdin)
    try:
        cprint(TITLE, '==>', title)
        items = {}
        for c, (n, t) in letterify(names):
            print('    ', c, t)
            items[c] = n
        for k, name in cmds.items():
            print('   ', ':'+k, name)
        tty.setcbreak(sys.stdin)
        ch = sys.stdin.read(1)
        if ch == ':':
            sys.stdout.write(':')
            sys.stdout.flush()
            tty.tcsetattr(sys.stdin, tty.TCSADRAIN, attr)
            cmd = sys.stdin.readline()
            parts = cmd.strip().split(None, 1)
            raise CommandExecute(*parts)
        elif ch in items:
            return items[ch]
    finally:
        tty.tcsetattr(sys.stdin, tty.TCSADRAIN, attr)


