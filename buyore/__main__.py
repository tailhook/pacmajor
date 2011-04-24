import urllib.request
import os
import sys
import shutil

from .rorepo import load_repos, local_repo
from .dep import DependencyChecker
from .display import (CommandExecute,
    action, section, title, print_item, menu, pkgfile)
from . import display
from . import aur
from . import pacman
from . import pkgbuild
from .util import runcommand

REPO_DIR = '/var/lib/pacman/sync'

def install_packages(names):
    stock = {}
    with action("Reading local repositories"):
        localrepo = local_repo()
    with action('Searching for stock packages') as act:
        repos = load_repos()
        for r in repos.values():
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
    with pkgbuild.tmpdb() as pdb:
        with section('Gathering PKGBUILDs and dependencies') as act:
            dep = DependencyChecker(builds.keys())
            dep.check(pdb)
        if dep.stock_deps:
            title("Installing following packages")
            for pkg in dep.stock_deps:
                print_item(pkg.name)
        all_files = []
        modes = {}
        for pkg in dep.aur_deps + dep.targetpkgs:
            for fn in pkg.files_to_edit():
                all_files.append((pkg.name, fn))
        while True:
            try:
                res = menu("Files to look throught from AUR",
                    (((pn, fn),
                      pkgfile(modes.get((pn, fn), display.FILE_NEW), pn, fn))
                     for pn, fn in all_files),
                    e="NAME     change editor ({EDITOR})".format_map(os.environ),
                    d="LETTERS  diff files",
                    q="         quit")
            except KeyboardInterrupt:
                res = ('q',)
            except CommandExecute as cmd:
                if cmd.name == 'e':
                    os.environ['EDITOR'] = cmd.arg
                elif cmd.name == 'setdiff':
                    os.environ['DIFFTOOL'] = cmd.arg
                elif cmd.name == 'q':
                    sys.exit(2)
                elif cmd.name == 'done':
                    break
                elif cmd.name in ('d', 'diff', 'dall', 'diffall', 'diff_all'):
                    if (cmd.arg == 'all'
                        or cmd.name in ('dall', 'diffall', 'diff_all')):
                        for pn, fn in all_files:
                            rn = os.path.join(pdb.dir, pn, fn)
                            runcommand([os.environ["DIFFTOOL"],
                                '-uw', rn+'.orig', rn])
                    else:
                        chars = dict(display.letterify(all_files))
                        for c in cmd.arg:
                            try:
                                pn, fn = chars[c]
                            except KeyError:
                                continue
                            rn = os.path.join(pdb.dir, pn, fn)
                            runcommand([os.environ["DIFFTOOL"],
                                '-uw', rn+'.orig', rn])
            else:
                if not res:
                    continue
                fn = os.path.join(pdb.dir, *res)
                if not os.path.exists(fn+'.orig'):
                    shutil.copy(fn, fn+'.orig')
                runcommand([os.environ['EDITOR'], fn])
                if runcommand(['diff', '-qw', fn, fn+'.orig']) == 0:
                    modes[res] = display.FILE_VIEWED
                else:
                    modes[res] = display.FILE_MODIFIED

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

    os.environ.setdefault('EDITOR', 'vim')
    if display.colorize:
        os.environ.setdefault('DIFFTOOL', 'colordiff')
    else:
        os.environ.setdefault('DIFFTOOL', 'diff')

    if options.packages:
        install_packages(options.packages)

if __name__ == '__main__':
    main()
