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
    return ap

def main():
    from . import display
    global options

    ap = get_options()
    options = ap.parse_args()

    manager = core.Buyore(
        interactive=options.interactive,
        verbosity=options.verbosity,
        root=options.root,
        color=options.color)

    if options.packages:
        manager.install_packages(options.packages)

if __name__ == '__main__':
    main()
