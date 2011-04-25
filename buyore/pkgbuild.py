import tempfile
import shutil
import os.path

import archive

from . import parser
from . import display

class PkgBuild(object):

    def __init__(self, file):
        self.vars = parser.parse_vars(file)
        self.pkgver = self.vars['pkgver']
        self.pkgrel = self.vars['pkgrel']
        self.pkgname = self.vars['pkgname']
        self.makedepends = [k.split('>=')[0]
            for k in self.vars.get('makedepends', ())]
        self.depends = [k.split('>=')[0]
            for k in self.vars.get('makedepends', ())]
        self.name = self.vars['pkgname']
        self.install = self.vars.get('install')

    def __repr__(self):
        return '<PKGBUILD {0}>'.format(self.name)

    def files_to_edit(self):
        yield 'PKGBUILD'
        if self.install:
            yield self.install

class TemporaryDB(object):

    def __init__(self, manager):
        self.manager = manager
        self.states = {}
        self.packages = {}
        makepkgconf = os.path.join(self.manager.root, 'etc/makepkg.conf')
        with open(makepkgconf, 'rb') as file:
            self.config = parser.parse_vars(file)

    def __enter__(self):
        self.dir = tempfile.mkdtemp()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        shutil.rmtree(self.dir)

    def fetch(self, name):
        tarurl = 'http://aur.archlinux.org/packages/{0}/{0}.tar.gz'\
            .format(name)
        tarname = '{0}/{1}.tar.gz'.format(self.dir, name)
        self.manager.toolset.download(output=tarname, url=tarurl)
        self.manager.toolset.unpack(outdir=self.dir, filename=tarname)
        with open('{0}/{1}/PKGBUILD'.format(self.dir, name), 'rb') as f:
            pkg = PkgBuild(f)
        self.packages[name] = pkg
        return pkg

    def file_backup(self, pkg, file, *, suffix='.orig'):
        fn = os.path.join(self.dir, pkg, file)
        if not os.path.exists(fn+'.orig'):
            shutil.copy(fn, fn+'.orig')

    def file_path(self, pkg, file):
        return os.path.join(self.dir, pkg, file)

    def file_get_state(self, pkg, file):
        return self.states.get((pkg, file), display.FILE_NEW)

    def file_check_state(self, pkg, file, *, backup_suffix='.orig'):
        fn = os.path.join(self.dir, pkg, file)
        if self.manager.toolset.compare(fn, fn+backup_suffix) == 0:
            self.states[pkg, file] = display.FILE_VIEWED
        else:
            self.states[pkg, file] = display.FILE_MODIFIED

    def build_package(self, name):
        with self.manager.section("Building " + name) as sect:
            self.manager.toolset.build(
                cwd=os.path.join(self.dir, name))
            nfiles = 0
            nbytes = 0
            for file in archive.Archive(self.package_file(name)):
                if name.startswith('.'):  # all hidden in the root are special
                    continue
                nfiles += 1
                nbytes += len(file.read())  # TODO: get size from libarchive

        self.packages[name].build_info = {
            'files': nfiles,
            'unpacked': nbytes,
            'elapsed': sect.elapsed,
            }

    def package_file(self, name):
        pkg = self.packages[name]
        return os.path.join(self.dir, name,
            '{0.pkgname}-{0.pkgver}-{0.pkgrel}-{1[CARCH]}{1[PKGEXT]}'
            .format(pkg, self.config))

def tmpdb(manager):
    return TemporaryDB(manager)
