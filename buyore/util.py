import subprocess
from .display import commandline

def runcommand(cmdline):
    commandline(cmdline)
    return subprocess.call(cmdline)
