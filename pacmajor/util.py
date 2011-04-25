import subprocess
import shlex
import os

class Tool(object):
    """Single tool that runs from a command-line

    :param cmdline: command-line to run
    :type cmdline: string
    :param pager: pager tool, None if not applicable
    :type pager: :class:`Tool`
    """
    def __init__(self, cmdline, manager, pager=None):
        self.manager = manager
        self.pager = pager
        self.update(cmdline)

    def update(self, cmdline):
        self.cmdline = shlex.split(cmdline)
        self.indexes = {arg[1:]: i
            for i, arg in enumerate(self.cmdline)
            if arg.startswith('$')}

    def __call__(self, *args, **kw):
        """Execute the tool with pager if needed"""
        cmdline = list(self.cmdline)
        cmdline.extend(args)
        filter = kw.pop('filter', None)
        cwd = kw.pop('cwd', None)
        for k, v in kw.items():
            cmdline[self.indexes[k]] = v
        self.manager.commandline(cmdline)
        if filter:
            proc = subprocess.Popen(cmdline, stdout=filter.stdin, cwd=cwd)
            return proc.wait()
        elif self.pager and self.pager.enabled:
            proc = subprocess.Popen(cmdline, stdout=subprocess.PIPE, cwd=cwd)
            self.pager.filter(proc.stdout)
            return proc.wait()
        else:
            proc = subprocess.Popen(cmdline, cwd=cwd)
            return proc.wait()

    def filter(self, pipe=None):
        """Filter data through tool"""
        if pipe is None:
            return subprocess.Popen(self.cmdline, stdin=subprocess.PIPE)
        else:
            return subprocess.Popen(self.cmdline, stdin=pipe).wait()

class Toolset(object):

    def __init__(self, manager, interactive=True):
        self.manager = manager
        self.tools = {}
        self.declare_tool('pager', 'less -R')
        self.tools['pager'].enabled = interactive
        self.declare_tool('editor', 'vim')
        diff = 'colordiff -uw' if interactive else 'diff -uw'
        self.declare_tool('diff', diff, pager=True)
        self.declare_tool('compare', 'diff -qw')
        pacman = 'pacman -S' if os.getuid() == 0 else 'sudo pacman -S'
        self.declare_tool('install_sync', pacman)
        pacman = 'pacman -U' if os.getuid() == 0 else 'sudo pacman -U'
        self.declare_tool('install_file', pacman)
        self.declare_tool('download', 'wget -nv -O $output $url')
        self.declare_tool('unpack', 'bsdtar -xf $filename -C $outdir')
        self.declare_tool('build', 'makepkg --log')
        self.declare_tool('namcap', 'namcap')
        self.declare_tool('sed', 'sed -i')
        self.declare_tool('git', 'git')

    def declare_tool(self, name, default, pager=False):
        cmdline = default
        self.manager.debug("Tool `{0}`, default: {1}".format(name, cmdline))
        if name in self.manager.config:
            cmdline = self.manager.config[name]
            self.manager.debug("Tool `{0}`, from config: {1}"
                .format(name, cmdline))
        if name.upper() in os.environ:
            cmdline = os.environ[name.upper()]
            self.manager.debug("Tool `{0}`, environ {1}: {2}"
                .format(name, name.upper(), cmdline))
        if 'PACMAJOR_'+name.upper() in os.environ:
            cmdline = os.environ['PACMAJOR_'+name.upper()]
            self.manager.debug("Tool `{0}`, environ PACMAJOR_{1}: {2}"
                .format(name, name.upper(), cmdline))
        self.manager.tool_selected(name, cmdline)
        self.tools[name] = Tool(cmdline, manager=self.manager,
            pager=self.tools['pager'] if pager else None)

    def update(self, name, cmdline):
        self.tools[name].update(cmdline)

    def __getattr__(self, name):
        try:
            return self.tools[name]
        except KeyError:
            raise AttributeError(name)
