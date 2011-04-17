import subprocess
from .display import commandline

def install(names):
    cmdline = ['sudo', 'pacman', '-S'] + names
    commandline(cmdline)
    subprocess.Popen(cmdline).wait()

