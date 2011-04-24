import os.path
from collections import defaultdict

import archive

LOCAL_REPO = 'var/lib/pacman/local'
REPO_DIR = 'var/lib/pacman/sync'

def parse_properties(f):
    body = f.read()
    items = body.split(b'\n\n')
    entry = {}
    for item in items:
        if not item:
            continue  # end of text
        if not b'\n' in item:
            entry[item[1:-1].lower().decode('ascii')] = b""
        else:
            k, v = item.split(b'\n', 1)
            entry[k[1:-1].lower().decode('ascii')] = v
    return entry

class Package(object):

    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)
        self.name = self.name.decode('utf-8')
        self.replaces = [a.decode('ascii')
            for a in getattr(self, 'replaces', "").splitlines()]
        self.provides = [a.decode('ascii')
            for a in getattr(self, 'provides', "").splitlines()]

class Repo(object):

    def __init__(self):
        self.packages = {}
        self.names = defaultdict(list)

    def add_package(self, p):
        self.packages[p.name] = p
        self.names[p.name].append(p)
        for i in p.replaces:
            self.names[i].append(p)
        for i in p.provides:
            self.names[i].append(p)


class LocalRepo(Repo):
    def __init__(self, root):
        super().__init__()
        dir = root + LOCAL_REPO
        for rawname in os.listdir(dir):
            with open(os.path.join(dir, rawname, 'desc'), 'rb') as file:
                entry = parse_properties(file)
            with open(os.path.join(dir, rawname, 'files'), 'rb') as file:
                entry.update(parse_properties(file))
            self.add_package(Package(**entry))

class ReadonlyRepo(Repo):

    def __init__(self, filename):
        super().__init__()
        arch = archive.Archive(filename)
        all = {}
        for f in arch:
            entry = parse_properties(f)
            pkgname = f.filename.rsplit('/', 1)[0]
            if pkgname in all:
                all[pkgname].update(entry)
            else:
                all[pkgname] = entry
        for namever, props in all.items():
            p = Package(**props)
            self.add_package(p)

def load_repos(root):
    repos = {}
    for i in os.listdir(root + REPO_DIR):
        repos[i] = ReadonlyRepo(root + REPO_DIR+'/'+i)
    return repos

