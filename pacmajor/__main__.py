from . import core

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
        dest="interactive", default=False, action='store_false')  # TODO: auto
    ap.add_argument('-v', '--verbose', nargs=0,
        help="Increase verbosity",
        dest="verbosity", default=1, action=increment)
    ap.add_argument('-q', '--quiet', nargs=0,
        help="Decrease verbosity",
        dest="verbosity", action=decrement)
    ap.add_argument('--color',
        help="Colorize output",
        dest="color", default=True, action="store_true")
    ap.add_argument('-C', '--no-color',
        help="Do not colorize output",
        dest="color", action="store_false")
    ap.add_argument('-r', '--root',
        help="Alternative installation root",
        dest="root", default="/")
    ap.add_argument('-k', '--keep-files',
        help="Keep temporary files needed to build package",
        dest="keep_files", default=False, action="store_true")
    action = ap.add_mutually_exclusive_group()
    action.add_argument('-P', '--git-pull-push', metavar="TARGET",
        help="Pull remote changes and push our changes",
        dest="backup", default=None, nargs='*')
    return ap

def main():
    from . import display
    global options

    ap = get_options()
    options = ap.parse_args()

    manager = core.Pacmajor(
        interactive=options.interactive,
        verbosity=options.verbosity,
        root=options.root,
        keep_files=options.keep_files,
        color=options.color)

    if options.backup is not None:
        manager.backup_git(targets=options.backup or None,
            packages=options.packages or None)
    else:
        if options.packages:
            manager.install_packages(options.packages)

if __name__ == '__main__':
    main()
