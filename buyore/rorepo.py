import tarfile

class ReadonlyRepo(object):

    def __init__(self, filename):
        arch = tarfile.open(filename)
        all = {}
        for f in arch:
            ff = arch.extractfile(f)
            if not ff:
                continue # probably dir
            body = ff.read()
            items = body.split(b'\n\n')
            entry = {}
            for item in items:
                if not item:
                    continue  # end of text
                if not b'\n' in item:
                    entry[item[1:-1].lower()] = b''
                else:
                    k, v = item.split(b'\n', 1)
                    entry[k[1:-1].lower()] = v
            pkgname = f.name.rsplit('/', 1)[0]
            if pkgname in all:
                all[pkgname].update(entry)
            else:
                all[pkgname] = entry
