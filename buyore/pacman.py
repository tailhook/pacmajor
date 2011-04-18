from .util import runcommand

def install(names):
    runcommand(['sudo', 'pacman', '-S'] + names)

