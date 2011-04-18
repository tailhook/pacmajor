import urllib.request
import os

from .rorepo import ReadonlyRepo
from .display import action, section, title
from . import aur
from . import pacman
from . import pkgbuild

REPO_DIR = '/var/lib/pacman/sync'

def load_repos():
    repos = []
    for i in os.listdir(REPO_DIR):
        repos.append(ReadonlyRepo(REPO_DIR+'/'+i))
    return repos

def install_packages(names):
    stock = {}
    all_stock = set()
    with action('Searching for stock packages') as act:
        repos = load_repos()
        for r in repos:
            all_stock.update(r.packages)
            for n in names:
                p = r.packages.get(n)
                if p is not None:
                    stock[n] = p
        act.add('found {0}'.format(len(stock)))

    builds = {}
    if set(names) - set(stock):
        with action('Searching in AUR') as act:
            for n in names:
                try:
                    info = aur.request('info', n)
                except LookupError:
                    continue
                builds[n] = info
            act.add('found {0}'.format(len(builds)))
    else:
        if options.verbosity:
            title("All names found in packages, starting pacman")
        pacman.install(names)
        return
    with section('Gathering PKGBUILDs and dependencies') as act:
        with pkgbuild.tmpdb() as pdb:
            future = list(builds.keys())
            already = set(future)
            stock_deps = []
            targets = []
            deps = []
            while future:
                name = future.pop()
                if name in all_stock:
                    stock_deps.add(name)
                    continue
                pkg = pdb.fetch(name)
                for dep in pkg.makedeps:
                    if dep in already:
                        continue
                    future.append(dep)
                for dep in pkg.depends:
                    if dep in already:
                        continue
                    future.append(dep)
                if pkg.name in builds:
                    targets.append(pkg)
                else:
                    deps.append(pkg)
        print("Stock depedencies", stock_deps)
        print("AUR dependencies", deps)
        print("Targets", targets)

def get_options():
    import argparse

    class increment(argparse.Action):
        def __call__(self, parser, ns, values, optstr=None):
            setattr(ns, self.dest, getattr(ns, self.dest) + 1)

    class decrement(argparse.Action):
        def __call__(self, parser, ns, values, optstr=None):
            setattr(ns, self.dest, getattr(ns, self.dest) - 1)

    ap = argparse.ArgumentParser()
    ap.add_argument(
        help="Packages to install",
        dest="packages", nargs="*", default=[])
    ap.add_argument('--batch',
        help="Disable interactive mode",
        dest="interactive", default=True, action='store_false')  # TODO: auto
    ap.add_argument('-v', '--verbose', nargs=0,
        help="Increase verbosity",
        dest="verbosity", default=1, action=increment)
    ap.add_argument('-q', '--quiet', nargs=0,
        help="Decrease verbosity",
        dest="verbosity", action=decrement)
    ap.add_argument('--color',
        help="Colorize output",
        dest="colorize", default=True, action="store_true")
    ap.add_argument('-C', '--no-color',
        help="Do not colorize output",
        dest="colorize", action="store_false")
    return ap

def main():
    from . import display
    global options

    ap = get_options()
    options = ap.parse_args()

    display.verbosity = options.verbosity
    display.colorize = options.colorize

    if options.packages:
        install_packages(options.packages)

if __name__ == '__main__':
    main()
