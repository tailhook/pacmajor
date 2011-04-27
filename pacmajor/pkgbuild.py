import tempfile
import shutil
import os.path
from functools import partial

import archive

from . import parser
from . import display

GIT_IGNORE = """
*.swo
*.swp
*~
*.orig
*.bak
"""

class PackageNotFound(Exception):
    pass

class PkgBuild(object):

    def __init__(self, file):
        self.update(file)

    def update(self, file):
        self.vars = parser.parse_vars(file)
        self.pkgver = self.vars['pkgver']
        self.pkgrel = self.vars['pkgrel']
        self.pkgname = self.vars['pkgname']
        self.makedepends = [k.split('>=')[0]
            for k in self.vars.get('makedepends', ())]
        self.depends = [k.split('>=')[0]
            for k in self.vars.get('depends', ())]
        self.name = self.vars['pkgname']
        self.install = self.vars.get('install')
        self.source = self.vars.get('source', ())

    def __repr__(self):
        return '<PKGBUILD {0}>'.format(self.name)

    def files_to_edit(self):
        yield 'PKGBUILD'
        if self.install:
            yield self.install

    def source_files(self):
        yield 'PKGBUILD'
        if self.install:
            yield self.install
        for i in self.source:
            if '://' in source:
                continue
            yield i


class TemporaryDB(object):

    def __init__(self, manager):
        self.manager = manager
        self.states = {}
        self.packages = {}
        self.gitdir = self.manager.config['git_dir']
        self.gitbranch = self.manager.config['git_my_branch']
        makepkgconf = os.path.join(self.manager.root, 'etc/makepkg.conf')
        with open(makepkgconf, 'rb') as file:
            self.config = parser.parse_vars(file)

    def __enter__(self):
        self.dir = tempfile.mkdtemp()
        self.edir = os.path.join(self.dir, 'empty')
        os.mkdir(self.edir)
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        shutil.rmtree(self.dir)

    def fetch(self, name):
        if not os.path.exists(self.gitdir):
            os.makedirs(self.gitdir)
        pkgdir = os.path.join(self.gitdir, name)
        localgit = partial(self.manager.toolset.git,
            '--git-dir='+pkgdir,
            '--work-tree='+os.path.join(self.dir, name))
        if not os.path.exists(pkgdir):
            os.mkdir(pkgdir)
            self.manager.toolset.git('init', '--bare', pkgdir)
        tarurl = 'http://aur.archlinux.org/packages/{0}/{0}.tar.gz'\
            .format(name)
        tarname = '{0}/{1}.tar.gz'.format(self.dir, name)
        self.manager.toolset.download(output=tarname, url=tarurl)
        if not os.path.exists(tarname) or not os.path.getsize(tarname):
            if not self.manager.config.get('local_packages'):
                raise PackageNotFound(name)
            localdir = os.path.join(self.manager.config['local_packages'], name)
            if os.path.exists(localdir):
                with open(os.path.join(localdir, 'PKGBUILD'), 'rb') as f:
                    pkg = PkgBuild(f)
                os.mkdir(os.path.join(self.dir, name))
                for sname in pkg.source_files():
                    shutil.copyfile(os.path.join(localdir, sname),
                        os.path.join(self.dir, name, sname))
            else:
                raise PackageNotFound(name)
        else:
            self.manager.toolset.unpack(outdir=self.dir, filename=tarname)
        with open(os.path.join(self.dir, name, '.gitignore'), 'wt') as f:
            f.write(GIT_IGNORE)
        with open(os.path.join(self.dir, name, 'PKGBUILD'), 'rb') as f:
            pkg = PkgBuild(f)
        localgit('symbolic-ref', 'HEAD', 'refs/heads/aur')
        localgit('add', '.')
        localgit('commit',
            '-m', 'Package version {0.pkgver!r} from aur'.format(pkg))
        localgit('branch', self.gitbranch, 'aur')
        localgit('symbolic-ref', 'HEAD', 'refs/heads/'+self.gitbranch)
        self.packages[name] = pkg
        return pkg

    def merge(self, name, branch=None):
        for f in self.packages[name].files_to_edit():
            self.file_backup(name, f)
        pkgdir = os.path.join(self.gitdir, name)
        localgit = partial(self.manager.toolset.git,
            '--git-dir='+pkgdir,
            '--work-tree='+os.path.join(self.dir, name),
            cwd=os.path.join(self.dir, name))  #needed for stash
        if branch is None or branch == self.gitbranch:
            localgit('symbolic-ref', 'HEAD', 'refs/heads/aur')
            localgit('stash', 'save', 'starting merge')
            localgit('symbolic-ref', 'HEAD', 'refs/heads/'+self.gitbranch)
            localgit('reset', '--hard')
            localgit('merge', '--no-commit', 'aur')
            localgit('stash', 'pop')
        else:
            localgit('symbolic-ref', 'HEAD', 'refs/heads/'+self.gitbranch)
            localgit('merge', '--no-commit', branch)
        for f in self.packages[name].files_to_edit():
            self.file_check_state(name, f)

    def mergetool(self, name):
        pkgdir = os.path.join(self.gitdir, name)
        localgit = partial(self.manager.toolset.git,
            '--git-dir='+pkgdir,
            '--work-tree='+os.path.join(self.dir, name),
            cwd=os.path.join(self.dir, name))  #needed for mergetool
        localgit('mergetool')

    def commit(self, name, message):
        for f in self.packages[name].files_to_edit():
            self.file_backup(name, f)
        pkgdir = os.path.join(self.gitdir, name)
        localgit = partial(self.manager.toolset.git,
            '--git-dir='+pkgdir,
            '--work-tree='+os.path.join(self.dir, name))
        localgit('symbolic-ref', 'HEAD', 'refs/heads/'+self.gitbranch)
        localgit('add', '.')
        localgit('commit', '-m', message)
        for f in self.packages[name].files_to_edit():
            self.file_check_state(name, f)

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
            pobj = self.packages[pkg]
            try:
                with open(os.path.join(self.dir, pkg, 'PKGBUILD'), 'rb') as f:
                    pobj.update(f)
            except Exception as e:
                print(e)

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

    def buildlog_files(self, name):
        pkg = self.packages[name]
        yield os.path.join(self.dir, name,
            '{0.pkgname}-{0.pkgver}-{0.pkgrel}-{1[CARCH]}-build.log'
            .format(pkg, self.config))
        yield os.path.join(self.dir, name,
            '{0.pkgname}-{0.pkgver}-{0.pkgrel}-{1[CARCH]}-package.log'
            .format(pkg, self.config))

def tmpdb(manager):
    return TemporaryDB(manager)
