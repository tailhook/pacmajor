import archive

class Package(object):

    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)

class ReadonlyRepo(object):

    def __init__(self, filename):
        arch = archive.Archive(filename)
        all = {}
        for f in arch:
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
            pkgname = f.filename.rsplit('/', 1)[0]
            if pkgname in all:
                all[pkgname].update(entry)
            else:
                all[pkgname] = entry
        self.packages = {}
        for namever, props in all.items():
            p = Package(**props)
            self.packages[p.name.decode('ascii')] = p

