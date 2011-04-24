import sys
import os

from .display import CommandExecute, letterify

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
    cmddesc = []
    cmdhand = {}
    for funcname in dir(cls):
        if not funcname.startswith('cmd_'):
            continue
        fun = getattr(cls, funcname)
        aliases = fun.__annotations__.get('return')
        help = bool(aliases)
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
        if help:
            cmddesc.append((aliases[0], argname, fun.__doc__))
        cmd = _mkcmd(fun, cmdarg, argkey)
        for alias in aliases:
            cmdhand[alias] = cmd
    cls.command_descr = cmddesc
    cls.command_handlers = cmdhand
    return cls

@extractcommands
class PkgbuildMenu(object):
    def __init__(self, manager, pkgs, pkgdb):
        self.manager = manager
        self.pkgs = pkgs
        self.pkgdb = pkgdb
        self.all_files = []
        for pkg in self.pkgs:
            for fn in pkg.files_to_edit():
                self.all_files.append((pkg.name, fn))

    def completer(self, prefix, state):
        print("PREFIX", prefix, state)
        for i in cmdhand:
            if i.startswith(prefix):
                yield i

    def run(self):
        while True:
            try:
                self.manager.set_completer(self.completer)
                res = self.manager.menu("Files to look throught from AUR",
                    [((pn, fn),
                      self.manager.pkgfile(
                        self.pkgdb.file_get_state(pn, fn), pn, fn))
                      for pn, fn in self.all_files],
                    self.command_descr)
            except KeyboardInterrupt:
                res = ('q',)
            except CommandExecute as cmd:
                try:
                    func = self.command_handlers[cmd.name]
                except KeyError:
                    pass
                else:
                    func(self, cmd.name, cmd.arg)
            except DoneException as e:
                break
            else:
                if not res:
                    continue
                self.pkgdb.file_backup(*res)
                self.manager.toolset.editor(self.pkgdb.file_path(*res))
                self.pkgdb.file_check_state(*res)

    def cmd_editor(self, command:'NAME') -> 'e':
        """change editor"""
        self.manager.toolset.update('editor', command)

    def cmd_quit(self) -> 'q':
        """quit"""
        sys.exit(2)

    def cmd_setdiff(self, command:'COMMAND'):
        """set diff command"""
        self.manager.toolset.update('diff', command)

    def cmd_done(self) -> 'done':
        """build packages"""
        raise DoneException()

    diff_aliases = ('d', 'diff', 'dall', 'diffall', 'diff_all')
    def cmd_diff(self, cmd:'', letters:"LETTERS") -> diff_aliases:
        """show differences"""
        if self.manager.toolset.pager.enabled:
            pager = self.manager.toolset.pager.filter()
        if letters == 'all' or 'all' in cmd:
            for pn, fn in self.all_files:
                rn = self.pkgdb.file_path(pn, fn)
                if os.path.exists(rn + '.orig'):
                    self.manager.toolset.diff(rn+'.orig', rn, filter=pager)
        else:
            chars = dict(letterify(self.all_files))
            for c in letters or '':
                try:
                    pn, fn = chars[c]
                except KeyError:
                    continue
                rn = self.pkgdb.file_path(pn, fn)
                if os.path.exists(rn + '.orig'):
                    self.manager.toolset.diff(rn+'.orig', rn, filter=pager)
        pager.stdin.close()
        pager.wait()
