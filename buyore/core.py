from .util import Toolset
from .display import DisplayObject
from .dep import DependencyChecker
from .rorepo import LocalRepo, load_repos
from .ui import PkgbuildMenu
from . import aur
from . import pkgbuild

class Buyore(DisplayObject):
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
        self.toolset = Toolset(self)

    def load_local(self):
        self.localrepo = LocalRepo(self.root)

    def load_repos(self):
        self.repos = load_repos(self.root)

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
            if options.verbosity:
                self.title("All names found in packages, starting pacman")
            pacman.install(names)
            return
        with pkgbuild.tmpdb(self) as pdb:
            with self.section('Gathering PKGBUILDs and dependencies') as act:
                dep = DependencyChecker(builds.keys())
                dep.check(self, pdb)
            if dep.stock_deps:
                self.title("Installing following packages")
                for pkg in dep.stock_deps:
                    print_item(pkg.name)
            PkgbuildMenu(self, dep.aur_deps + dep.targetpkgs, pdb).run()
