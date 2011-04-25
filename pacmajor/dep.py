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

    def stage_sort(self):
        stages = []
        items = {pkg.name: pkg for pkg in self.targetpkgs + self.aur_deps}
        names = set(items)
        while names:
            cur = []
            for nn in list(names):
                pkg = items[nn]
                if not names & (set(pkg.depends) | set(pkg.makedepends)):
                    cur.append(nn)
                    names.remove(nn)
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
        return stages
