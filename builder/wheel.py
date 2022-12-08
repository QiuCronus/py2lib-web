import os
import sys

from .utils import shell


def rmdirs(dirpath):
    for root, dirs, names in os.walk(dirpath):
        for name in names:
            abspath = os.path.join(root, name)
            print("[+] Delete %s" % abspath)
            os.remove(abspath)


def bdist_wheel(dirpath):
    # type: (str) -> (bool, str | Exception)
    try:
        # os.chdir(dirpath)
        print("[+] folder: %s" % dirpath)

        dir_whl = os.path.join(dirpath, "dist")
        if not os.path.exists(dir_whl):
            os.makedirs(dir_whl)
        rmdirs(dir_whl)

        cmd = sys.executable + " setup.py -q bdist_wheel"
        exit_code, stdout, stderr = shell(cmd, cwd=dirpath)
        print("[+] command: python setup.py -q bdist_wheel")
        print("[+} exit_code: %s" % exit_code)
        for line in stdout:
            line = line.replace("\r", "").replace("\n", "").strip()
            print("[+] %s" % line)
        for line in stderr:
            line = line.replace("\r", "").replace("\n", "").strip()
            print("[*] %s" % line)
        whlfiles = os.listdir(dir_whl) or []
        if whlfiles:
            print("[+] wheel: %s" % whlfiles[0])

            return True, whlfiles[0]
        return False, "No egg file."
    except Exception as err:
        return False, err


if __name__ == "__main__":
    bdist_wheel(r"X:\Coding\src\cronusqiu\trunk\tools\py2lib-web\data\temps\44f404dcc12349c3b4239e7363bd9ad1")
