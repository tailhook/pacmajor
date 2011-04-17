import urllib.request
import os

from .rorepo import ReadonlyRepo
from .display import action, title
from . import aur
from . import pacman

REPO_DIR = '/var/lib/pacman/sync'

def load_repos():
    repos = []
    for i in os.listdir(REPO_DIR):
        repos.append(ReadonlyRepo(REPO_DIR+'/'+i))
    return repos

def install_packages(names):
    stock = {}
    with action('Searching for stock packages') as act:
        repos = load_repos()
        for r in repos:
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
    print("STOCK", stock)
    print("AUR", builds)

def get_options():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument(
        help="Packages to install",
        dest="packages", nargs="*", default=[])
    ap.add_argument('--batch',
        help="Disable interactive mode",
        dest="interactive", default=True, action='store_false')  # TODO: auto
    ap.add_argument('-v', '--verbose',
        help="Increase verbosity",
        dest="verbosity", default=1, action="store_true")
    ap.add_argument('-q', '--quiet',
        help="Decrease verbosity",
        dest="verbosity", action="store_false")
    return ap

def main():
    global options
    ap = get_options()
    options = ap.parse_args()
    if options.packages:
        install_packages(options.packages)

if __name__ == '__main__':
    main()
