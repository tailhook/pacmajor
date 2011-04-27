from collections import defaultdict

from . import rorepo
from .pkgbuild import PackageNotFound

class DependencyChecker(object):

    def __init__(self, targets):
        self.targets = targets
        self.installed_deps = []
        self.stock_deps = []
        self.aur_deps = []
        self.targetpkgs = []
        self.not_found = set()

    def check(self, manager, pkgdb):
        future = list(self.targets)
        already = set()
        localrepo = manager.localrepo
        all_stock = defaultdict(list)
        for k, v in manager.repos.items():
            all_stock[k].extend(v.names)
        while future:
            name = future.pop()
            if name in localrepo.names and not name in self.targets:
                self.installed_deps.append(name)
                continue
            if name in all_stock:
                self.stock_deps.append(name)
                continue
            try:
                pkg = pkgdb.fetch(name)
            except PackageNotFound:
                self.not_found.add(name)
                continue
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

    def stage_sort(self):
        stages = []
        items = {}
        names = set()
        for pkg in self.targetpkgs + self.aur_deps:
            items[pkg.name] = pkg
            names.add(pkg.name)
            names.update(pkg.provides)
        while names:
            cur = []
            for nn in items:
                pkg = items[nn]
                if not names & (set(pkg.depends) | set(pkg.makedepends)):
                    cur.append(nn)
            if not stages:
                stock = []
                aur = []
                for i in cur:
                    if isinstance(items[i], rorepo.Package):
                        stock.append(i)
                    else:
                        aur.append(i)
                if stock:
                    stages.append(('stock', stock))
                if aur:
                    stages.append(('aur', aur))
            else:
                stages.append(('aur', cur))
            for nn in cur:
                pkg = items.pop(nn)
                names.remove(pkg.name)
                names.difference_update(pkg.provides)
        return stages
