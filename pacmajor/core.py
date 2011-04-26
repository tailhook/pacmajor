import os.path

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

        builds = {}
        if set(names) - set(stock):
            with self.action('Searching in AUR') as act:
                for n in names:
                    try:
                        info = aur.request('info', n)
                    except LookupError:
                        continue
                    builds[n] = info
                act.add('found {0}'.format(len(builds)))
        else:
            if self.verbosity:
                self.title("All names found in packages, starting pacman")
            self.toolset.install_sync(*names)
            return
        with pkgbuild.tmpdb(self) as pdb:
            with self.section('Gathering PKGBUILDs and dependencies') as act:
                dep = DependencyChecker(builds.keys())
                dep.check(self, pdb)
            if dep.stock_deps:
                self.title("Installing following packages")
                for pkg in dep.stock_deps:
                    print_item(pkg.name)
            aurinfo = builds.copy()
            for pkg in dep.aur_deps:
                aurinfo[pkg] = aur.request('info', pkg.name)
            PkgbuildMenu(self, pdb, dep.aur_deps + dep.targetpkgs, builds).run()
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
                    normal = [pdb.package_file(p) for p in pkgs if p in builds]
                    deps = [pdb.package_file(p) for p in pkgs if p not in builds]
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
