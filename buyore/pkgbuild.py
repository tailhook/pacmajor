import tempfile
import shutil
from tokenize import tokenize

from .util import runcommand

class PkgBuild(object):
    def __init__(self, file):
        for (typ, val, (row, col), (er, ec), ln) in tokenize(file.readline):
            pass

class TemporaryDB(object):
    def __init__(self):
        pass

    def __enter__(self):
        self.dir = tempfile.mkdtemp()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        shutil.rmtree(self.dir)

    def fetch(self, name):
        tarurl = 'http://aur.archlinux.org/packages/{0}/{0}.tar.gz'\
            .format(name)
        tarname = '{0}/{1}.tar.gz'.format(self.dir, name)
        runcommand(['wget', '-nv', '-O', tarname, tarurl])
        runcommand(['bsdtar', '-xf', tarname, '-C', self.dir])
        with open('{0}/{1}/PKGBUILD'.format(self.dir, name), 'rb') as f:
            return PkgBuild(f)

def tmpdb():
    return TemporaryDB()
