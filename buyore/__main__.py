import urllib.request
import os

from .rorepo import ReadonlyRepo

REPO_DIR = '/var/lib/pacman/sync'

def load_repos():
    repos = []
    for i in os.listdir(REPO_DIR):
        repos.append(ReadonlyRepo(REPO_DIR+'/'+i))
    return repos

def install_packages(names):
    repos = load_repos()
    for r in repos:
        for p in r.packages:
            if p in names:
                print(p)

def get_options():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument(
        help="Packages to install",
        dest="packages", nargs="*", default=[])
    ap.add_argument('--batch',
        help="Disable interactive mode",
        dest="interactive", default=True, action='store_false')  # TODO: auto
    return ap

def main():
    ap = get_options()
    options = ap.parse_args()
    if options.packages:
        install_packages(options.packages)

if __name__ == '__main__':
    main()
