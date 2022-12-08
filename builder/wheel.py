import os
import subprocess


def bdist_wheel(dirpath):
    os.chdir(dirpath)
    try:
        proc = subprocess.Popen(
            f"python setup.py bdist_wheel", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        proc.wait()
        return True, None
    except Exception as err:
        return False, err
