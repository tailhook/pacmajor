import subprocess
from .display import commandline

def runcommand(cmdline):
    commandline(cmdline)
    subprocess.Popen(cmdline).wait()
