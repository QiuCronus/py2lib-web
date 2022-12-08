import subprocess
import sys
import os


def shell(cmd, cwd):
    if sys.version_info >= (3, 7):
        proc = subprocess.Popen(
            cmd,
            shell=True,
            cwd=cwd,
            env=os.environ.copy(),
            text=True,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
    else:
        proc = subprocess.Popen(
            cmd,
            shell=True,
            cwd=cwd,
            env=os.environ.copy(),
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
    proc.wait(timeout=120)
    return proc.returncode, proc.stdout.readlines(), proc.stderr.readlines()
