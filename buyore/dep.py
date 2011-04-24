from collections import defaultdict

from . import rorepo

class DependencyChecker(object):

    def __init__(self, targets):
        self.targets = targets
        self.installed_deps = []
        self.stock_deps = []
        self.aur_deps = []
        self.targetpkgs = []

    def check(self, manager, pkgdb):
        future = list(self.targets)
        already = set(future)
        localrepo = manager.localrepo
        all_stock = defaultdict(list)
        for k, v in all_stock.items():
            all_stock[k].extend(v)
        while future:
            name = future.pop()
            if name in localrepo.names:
                self.installed_deps.append(name)
                continue
            if name in all_stock:
                self.stock_deps.append(name)
                continue
            pkg = pkgdb.fetch(name)
            for dep in pkg.makedepends:
                if dep in already:
                    continue
                future.append(dep)
            for dep in pkg.depends:
                if dep in already:
                    continue
                future.append(dep)
            if pkg.name in self.targets:
                self.targetpkgs.append(pkg)
            else:
                self.aur_deps.append(pkg)
