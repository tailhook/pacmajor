import sys
import os

import archive

from .display import Menu, DoneException, extractcommands

@extractcommands
class PkgbuildMenu(Menu):
    visible_commands = ['done', 'd', 'e', 'h', 'q']

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

    def cmd_namcap(self, letters:'LETTERS') -> 'namcap':
        """check PKGBUILD with namcap"""
        print(list(self.letters_to_names(letters)))
        self.manager.toolset.namcap(*(self.pkgdb.file_path(*item)
            for item in self.letters_to_names(letters)))

    def cmd_bump(self, arg:'LET VER') -> ('up', 'bump', 'ver', 'version'):
        """change version (also set pkgrel to 1)"""
        if not arg:
            return
        let, ver = arg.split(None, 1)
        for i in self.letters_to_names(let):
            self.pkgdb.file_backup(*i)
            self.manager.toolset.sed(
                '{s/^pkgver=.*/pkgver=' + ver+'/;s/^pkgrel=.*/pkgrel=1/}',
                self.pkgdb.file_path(*i))
            self.pkgdb.file_check_state(*i)

    def cmd_newrel(self, let:'LETTERS') -> ('nrel', 'newrelease', 'nr'):
        """increment pkgrel number"""
        for i in self.letters_to_names(let):
            self.pkgdb.file_backup(*i)
            pkg = self.pkgdb.packages[i[0]]
            self.manager.toolset.sed(
                '{s/^pkgrel=.*/pkgrel='+str(int(pkg.pkgrel)+1)+'/}',
                self.pkgdb.file_path(*i))
            self.pkgdb.file_check_state(*i)

    def cmd_done(self) -> 'done':
        """build packages"""
        raise DoneException()

    def cmd_merge(self, arg:'LET BRANCH') -> 'm':
        """merge branch"""
        try:
            let, branch = (arg or '').split(None, 1)
        except ValueError:
            let = arg
            branch = None
        merged = set()
        for i in self.letters_to_names(let):
            if i[0] in merged:
                continue
            merged.add(i[0])
            self.pkgdb.merge(i[0], branch)

    def cmd_mergetool(self, let:'LETTERS') -> ('mt', 'mtool'):
        """run git mergetool"""
        for i in self.letters_to_names(let):
            self.pkgdb.mergetool(i[0])

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
            for pn, fn in self.letters_to_names(letters):
                rn = self.pkgdb.file_path(pn, fn)
                if os.path.exists(rn + '.orig'):
                    self.manager.toolset.diff(rn+'.orig', rn, filter=pager)
        pager.stdin.close()
        pager.wait()

@extractcommands
class InstallMenu(Menu):
    visible_commands = ['inst', 'l', 'c', 'q']

    def __init__(self, manager, pkgdb, names):
        super().__init__(manager, "Just built packages")
        self.names = list(names)
        self.pkgdb = pkgdb

    def items(self):
        for name in self.names:
            pkg = self.pkgdb.packages[name]
            yield name, self.manager.pkgname(name, pkg.build_info)

    def select(self, name):
        pass

    def cmd_install(self) -> 'inst':
        """install packages"""
        raise DoneException()

    def cmd_list(self, letters:'LETTERS') -> 'l':
        """list package contents"""
        for name in self.letters_to_names(letters):
            for fn in archive.Archive(self.pkgdb.package_file(name)):
                print(name + ':', fn.filename)

    def cmd_namcap(self, letters:'LETTERS') -> ('c', 'namcap'):
        """check package with namcap"""
        self.manager.toolset.namcap(*(self.pkgdb.package_file(name)
            for name in self.letters_to_names(letters)))

    def cmd_quit(self) -> 'q':
        """quit"""
        sys.exit(2)
