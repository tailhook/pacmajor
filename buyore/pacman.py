import subprocess

def install(names):
    subprocess.Popen(['sudo', 'pacman', '-S'] + names).wait()

