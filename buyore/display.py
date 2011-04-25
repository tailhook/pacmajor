
__all__ = (
    'action',
    'title',
    )

import sys
import tty
import time

TITLE = b'32'
CMDLINE = b'34'
DEBUG = b'34'
RESET = b'\033[0m'
LETTERS = 'abcdefghijklmnoprstuvwxyz'

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

class DisplayObject(object):

    def cprint(self, color, *args, **kw):
        if not self.verbosity:
            return
        if self.color:
            ff = kw.get('file', sys.stdout).buffer
            ff.write(b'\033[' + color + b'm')
        print(*args, **kw)
        if self.color:
            ff.write(RESET)
            ff.flush()

    def pkgfile(self, mode, pkgname, fn):
        if self.color:
            if fn == 'PKGBUILD':
                return modes[mode]+' \033[37m' + pkgname + '\033[34m/' + fn + '\033[0m'
            else:
                return modes[mode]+' '+' '*len(pkgname) + ' \033[34m' + fn + '\033[0m'
        else:
            return modes[mode]+' ' + pkgname + '/' + fn

    def title(self, value):
        if self.verbosity:
            self.cprint(TITLE, '==>', value)

    def commandline(self, cmdline):
        if self.verbosity >= 2:
            self.cprint(CMDLINE, '  !', *cmdline)

    def print_item(self, *a, **kw):
        print('   ', *a, **kw)

    def debug(self, *a, **kw):
        if self.verbosity > 2:
            self.cprint(DEBUG, '  -', *a, **kw)

    def tool_selected(self, name, cmdline):
        if self.verbosity > 1:
            self.cprint(CMDLINE, '  *',
                'Tool `{0}`, selected:'.format(name), cmdline)

    def set_completer(self, func):
        import readline
        readline.parse_and_bind('tab: complete')
        readline.set_completer(func)

    def menu(self, title, names, cmds=None):
        attr = tty.tcgetattr(sys.stdin)
        try:
            self.cprint(TITLE, '==>', title)
            items = {}
            for c, (n, t) in letterify(names):
                print('    ', c, t)
                items[c] = n
            if cmds:
                mlen = max(len(mv)+len(k) for k, mv, name in cmds) + 1
                for k, mv, name in cmds:
                    print('    :{0:{1}} {2}'.format(k+' '+mv, mlen, name))
            tty.setcbreak(sys.stdin)
            ch = sys.stdin.read(1)
            if ch == ':':
                tty.tcsetattr(sys.stdin, tty.TCSADRAIN, attr)
                cmd = input(':')
                parts = cmd.strip().split(None, 1)
                if not parts:
                    return None
                raise CommandExecute(*parts)
            elif ch in items:
                return items[ch]
        finally:
            tty.tcsetattr(sys.stdin, tty.TCSADRAIN, attr)

    def action(self, title):
        return Action(self, title)

    def section(self, title):
        return Section(self, title)


class Action(object):

    def __init__(self, disp, title):
        self.disp = disp
        self.title = title
        self._inside = False
        self._time = None

    def __enter__(self):
        if self._time:
            raise RuntimeError("Can't enter same action twice")
        self.disp.cprint(TITLE, '==>', self.title, end=' ... ')
        self._time = time.time()
        return self

    def __exit__(self, exc_type, exc_value, ext_tb):
        d = time.time() - self._time
        self.disp.cprint(TITLE, ' ... done in {:.2f}s'.format(d))

    def add(self, text):
        if not self._time:
            raise RuntimeError("Bad time for adding info")
        self.disp.cprint(TITLE, text, end=' ')

class Section(object):

    def __init__(self, disp, title):
        self.disp = disp
        self.title = title
        self._inside = False
        self._time = None

    def __enter__(self):
        if self._time:
            raise RuntimeError("Can't enter same action twice")
        self.disp.cprint(TITLE, '==>', self.title, end=' ...\n')
        self._time = time.time()
        return self

    def __exit__(self, exc_type, exc_value, ext_tb):
        d = time.time() - self._time
        self.disp.cprint(TITLE, '--> done in {:.2f}s'.format(d))

    def add(self, text):
        if not self._time:
            raise RuntimeError("Bad time for adding info")
        self.disp.cprint(TITLE, '   ', text)


class DoneException(Exception):
    pass

def _mkcmd(fun, cmdarg, argkey):
    if cmdarg and argkey:
        def cmd(self, cmd, arg):
            return fun(self, **{cmdarg: cmd, argkey: arg})
    elif cmdarg:
        def cmd(self, cmd, arg):
            return fun(self, **{cmdarg: cmd})
    elif argkey:
        def cmd(self, cmd, arg):
            return fun(self, **{argkey: arg})
    else:
        def cmd(self, cmd, arg):
            return fun(self)
    return cmd

def extractcommands(cls):
    cmdall = []
    cmdhand = {}
    all = {}
    for funcname in dir(cls):
        if not funcname.startswith('cmd_'):
            continue
        fun = getattr(cls, funcname)
        aliases = fun.__annotations__.get('return')
        if not aliases:
            aliases = (funcname[len('cmd_'):],)
        elif isinstance(aliases, str):
            aliases = (aliases,)
        argname = ""
        argkey = None
        cmdarg = None
        for k, v in fun.__annotations__.items():
            if k == 'return':
                continue
            if isinstance(v, str):
                if v:
                    argkey = k
                    argname = v
                else:
                    cmdarg = k
        cmdall.append((aliases, argname, fun.__doc__))
        cmd = _mkcmd(fun, cmdarg, argkey)
        for alias in aliases:
            cmdhand[alias] = cmd
            all[alias] = (argname, fun.__doc__)
    cls.command_descr = [(a, ) + all[a] for a in cls.visible_commands]
    cls.command_alldescr = cmdall
    cls.command_handlers = cmdhand
    return cls

class Menu(object):

    def __init__(self, manager, title):
        self.manager = manager
        self.title = title

    def cmd_help(self) -> ('h', '?', 'help'):
        """show help"""
        mlen = max(len(mv)+len(a[0]) for a, mv, name in self.command_alldescr)+1
        for aliases, mv, name in self.command_alldescr:
            print('    :{0:{1}} {2}'.format(aliases[0]+' '+mv, mlen, name))
            if len(aliases) > 1:
                print('       aliases:', ', '.join(aliases))

    def completer(self, prefix, state):
        # TODO: explore why it doesn't get called
        for i in cmdhand:
            if i.startswith(prefix):
                yield i

    def letters_to_names(self, letters):
        if letters:
            mapping = dict(letterify(self.items()))
            for i in letters:
                item = mapping.get(i)
                if item is None:
                    continue
                yield item[0]
        else:
            for item in self.items():
                yield item[0]

    def run(self):
        while True:
            try:
                self.manager.set_completer(self.completer)
                res = self.manager.menu(self.title, self.items(),
                    self.command_descr)
            except KeyboardInterrupt:
                self.cmd_quit()
            except CommandExecute as cmd:
                try:
                    func = self.command_handlers[cmd.name]
                except KeyError:
                    pass
                else:
                    try:
                        func(self, cmd.name, cmd.arg)
                    except DoneException:
                        break
            else:
                if not res:
                    continue
                self.select(res)
