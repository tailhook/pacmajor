import sys
import os

from .display import Menu, DoneException, extractcommands, letterify

@extractcommands
class PkgbuildMenu(Menu):

    def __init__(self, manager, pkgdb, pkgs):
        super().__init__(manager, "Package files")
        self.pkgs = pkgs
        self.pkgdb = pkgdb
        self.all_files = []
        for pkg in self.pkgs:
            for fn in pkg.files_to_edit():
                self.all_files.append((pkg.name, fn))

    def items(self):
        for pn, fn in self.all_files:
            yield (pn, fn), self.manager.pkgfile(
                self.pkgdb.file_get_state(pn, fn), pn, fn)

    def select(self, res):
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

@extractcommands
class InstallMenu(object):
    def __init__(self, manager, pkgdb, names):
        self.manager = manager
        self.names = names
        self.pkgdb = pkgdb

    def run(self):
        pass

    def cmd_install(self) -> 'inst':
        """install packages"""
        raise DoneException()
