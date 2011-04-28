import os.path
import sys
import subprocess
import tempfile
import shutil

from .util import Toolset
from .display import DisplayObject
from .dep import DependencyChecker
from .rorepo import LocalRepo, load_repos
from .ui import PkgbuildMenu, InstallMenu
from . import aur
from . import pkgbuild
from . import parser

class Pacmajor(DisplayObject):
    """Represents whole package manager"""

    def __init__(self,
        interactive=True,
        verbosity=1,
        root='/',
        color=True):
        self.interactive = interactive
        self.verbosity = verbosity
        self.color = color
        self.root = root
        with open('/etc/pacmajor.conf', 'rb') as file:
            self.config = parser.parse_vars(file)
        self.toolset = Toolset(self)

    def load_local(self):
        self.localrepo = LocalRepo(self.root)

    def load_repos(self):
        self.repos = load_repos(self.root)
        val = self.config.get('ignore_repo')
        if val:
            if isinstance(val, str):
                self.repos.pop(val, None)
                self.repos.pop(val+'.db', None)
            else:
                for name in val:
                    self.repos.pop(name, None)
                    self.repos.pop(name+'.db', None)

    def backup_git(self, targets=None, packages=None):
        if targets is None:
            targets = self.config['git_backups']
        if not targets:
            print("Configure some targets in pacmajor.conf", file=sys.stderr)
            sys.exit(1)
        if packages is None:
            more = True
            packages = [n for n in os.listdir(self.config['git_dir'])
                          if not n.startswith('.')]
        else:
            more = False
        for tgt in targets:
            self.backup_single(tgt, packages, more=more)

    def backup_single(self, name, packages, more):
        packages = set(packages)
        url = self.config.get(name + '_url')
        branches = self.config.get(name + '_branches')
        pkglist = self.config.get(name + '_listpackages')
        newpack = self.config.get(name + '_newpackage')
        if not url or not branches or not pkglist:
            print(url, branches, pkglist)
            print("Target {0!r} configured incorrectly".format(name),
                file=sys.stderr)
            return
        remote_packages = set(subprocess.getoutput(pkglist).splitlines())
        if more:
            for i in remote_packages - packages:
                with self.section('Creating local {0}'.format(i)):
                    dir = os.path.join(self.config['git_dir'], i)
                    self.toolset.git('init', '--bare', dir)
        revbranches = []
        for branch in branches:
            r = ""
            if branch.startswith('+'):
                r = "+"
                branch = branch[1:]
            if ':' in branch:
                r = r+':'.join(reversed(branch.split(':', 1)))
            else:
                r = r+branch+':'+branch
            revbranches.append(r)
        for i in remote_packages & packages:
            with self.section('Pulling package {0}'.format(i)):
                dir = os.path.join(self.config['git_dir'], i)
                self.toolset.git('--git-dir='+dir,
                    'fetch', url.replace('$pkgname', i), *revbranches)
                #tmpdir = tempfile.mkdtemp()
                #try:
                #    self.toolset.git('--git-dir='+dir, '--work-tree='+tmpdir,
                #        'pull', '--ff-only',
                #        url.replace('$pkgname', i), *revbranches, cwd=tmpdir)
                #finally:
                #    shutil.rmtree(tmpdir)
        if more:
            packages.update(remote_packages)
        if newpack:
            for i in packages - remote_packages:
                with self.section('Creating remote {0}'.format(i)):
                    os.system(newpack.replace('$pkgname', i))
                    remote_packages.add(i)
        for i in remote_packages & packages:
            with self.section('Pushing changes of {0}'.format(i)):
                dir = os.path.join(self.config['git_dir'], i)
                self.toolset.git('--git-dir='+dir, 'push',
                    url.replace('$pkgname', i), *branches)

    def install_packages(self, names):
        stock = {}
        with self.action("Reading local repositories"):
            self.load_local()
        with self.action('Searching for stock packages') as act:
            self.load_repos()
            for r in self.repos.values():
                for n in names:
                    p = r.packages.get(n)
                    if p is not None:
                        stock[n] = p
            act.add('found {0}'.format(len(stock)))

        nbuild = set(names) - set(stock)
        if not nbuild:
            self.title("All names found in packages, starting pacman")
            self.toolset.install_sync(*names)
            return
        with pkgbuild.tmpdb(self) as pdb:
            with self.section('Gathering PKGBUILDs and dependencies') as act:
                dep = DependencyChecker(nbuild)
                dep.check(self, pdb)
            if dep.stock_deps:
                self.title("Installing following packages")
                for pkg in dep.stock_deps:
                    print_item(pkg.name)
            aurinfo = {}
            for pkg in dep.aur_deps + dep.targetpkgs:
                try:
                    aurinfo[pkg.name] = aur.request('info', pkg.name)
                except LookupError as e:
                    pass
            PkgbuildMenu(self, pdb, dep.aur_deps + dep.targetpkgs, aurinfo,
                absent_packages=dep.not_found).run()
            # TODO: recheck dependencies
            for pkg in dep.aur_deps + dep.targetpkgs:
                pdb.commit(pkg.name, "Edited package file")
            for typ, pkgs in dep.stage_sort():
                if typ == 'stock':
                    normal = [p for p in pkgs if p in stock]
                    deps = [p for p in pkgs if p not in stock]
                    if normal:
                        self.toolset.install_sync(*pkgs)
                    if deps:
                        self.toolset.install_sync('--asdeps', *pkgs)
                elif typ == 'aur':
                    for name in pkgs:
                        pdb.build_package(name)
                    InstallMenu(self, pdb, pkgs).run()
                    normal = [pdb.package_file(p) for p in pkgs if p in nbuild]
                    deps = [pdb.package_file(p) for p in pkgs if p not in nbuild]
                    if normal:
                        self.toolset.install_file(*normal)
                    if deps:
                        self.toolset.install_file('--asdeps', *deps)
                else:
                    raise NotImplementedError(typ)
            repodir = self.config.get('repo_dir')
            reponame = self.config.get('repo_name')
            if repodir and reponame:
                if not os.path.exists(repodir):
                    os.makedirs(repodir)
                for pkg in dep.aur_deps + dep.targetpkgs:
                    pfile = pdb.package_file(pkg.name)
                    tfile = os.path.join(repodir, os.path.basename(pfile))
                    self.toolset.copy(pfile, tfile)
                    self.toolset.repo_add(os.path.join(repodir,reponame), tfile)
