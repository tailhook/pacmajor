import tempfile
import shutil

from .util import runcommand
from . import parser

class PkgBuild(object):
    def __init__(self, file):
        values = {}
        for line in parser.parse(file):
            if isinstance(line, parser.VarValue):
                values[line.name.value] = line.interpolate(values)
        import pprint; pprint.pprint(values)
        self.vars = values
        self.makedepends = [k.split('>=')[0]
            for k in self.vars.get('makedepends', ())]
        self.depends = [k.split('>=')[0]
            for k in self.vars.get('makedepends', ())]
        self.name = self.vars['pkgname']

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
