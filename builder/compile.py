import os
import sys
import shutil
import platform
import subprocess
from configparser import ConfigParser
from dataclasses import dataclass, field

from builder.utils import shell

# base on https://github.com/cckuailong/py2sec


@dataclass
class Options:
    dir_root: str = ""
    exclude_files: set = field(default_factory=set)
    nthread: int = 1
    setup_script: str = ""
    pre_exist_libs: set = field(default_factory=set)


isWindows = True if platform.system() == "Windows" else False


def iter_files(dirpath, include_sub_folder=True, path_type=0, ext_names="*"):
    if isinstance(ext_names, str):
        if ext_names != "*":
            ext_names = [ext_names]
    if isinstance(ext_names, list):
        for i in range(len(ext_names)):
            ext_names[i] = ext_names[i].lower()

    def keep_file_by_ext(filename):
        if isinstance(ext_names, list):
            if filename[0] == ".":
                ext = filename
            else:
                ext = os.path.splitext(filename)[1]
            if ext.lower() not in ext_names:
                return False
        else:
            return True
        return True

    if include_sub_folder:
        len_of_root = len(dirpath)
        for root, dirs, names in os.walk(dirpath):
            for name in names:
                if not keep_file_by_ext(name):
                    continue
                if path_type == 0:
                    yield os.path.join(root, name)
                elif path_type == 1:
                    yield os.path.join(root[len_of_root:].lstrip(os.path.sep), name)
                else:
                    yield name
    else:
        for filename in os.listdir(dirpath):
            filepath = os.path.join(dirpath, filename)
            if os.path.isfile(filepath):
                if not keep_file_by_ext(filename):
                    continue
                if path_type == 0:
                    yield filepath
                else:
                    yield filename


def get_all_compile_files(opts: Options):
    should_compile_files = set()
    pyfiles = iter_files(opts.dir_root, include_sub_folder=True, path_type=1, ext_names=".py")
    for pyfile in pyfiles:
        filename = os.path.basename(pyfile)
        if filename in ["setup.py", "__init__.py", "_py2lib_.py"]:
            continue
        should_compile_files.add(pyfile)
    tmp_pyfiles = list(should_compile_files - opts.exclude_files)
    should_compile_files = []
    for pyfile in tmp_pyfiles:
        should_compile_files.append(pyfile)
    return sorted(should_compile_files)


def load_exclude_options(opts: Options):
    cfg_path = os.path.join(opts.dir_root, "py2lib.cfg")
    if not os.path.exists(cfg_path):
        return
    cfg = ConfigParser()
    cfg.read(cfg_path)
    if "options" in cfg.sections():
        if "exclude_files" in cfg.options("options"):
            exclude_files = cfg.get("options", "exclude_files") or ""
            exclude_files = [ef.strip() for ef in exclude_files.split("\n") if ef.strip()]
            for exclude_file in exclude_files:
                print(f"[+] Ignore: {exclude_file}")
                opts.exclude_files.add(os.path.normpath(exclude_file))
        if "exclude_dirs" in cfg.options("options"):
            exclude_dirs = cfg.get("options", "exclude_dirs") or ""
            exclude_dirs = [os.path.normpath(ed.strip()) for ed in exclude_dirs.split("\n") if ed.strip()]
            for exclude_dir in exclude_dirs:
                for pyfile in iter_files(opts.dir_root, include_sub_folder=True, path_type=1, ext_names=".py"):
                    if pyfile.startswith(exclude_dir):
                        print(f"[+] Ignore: {pyfile}")
                        opts.exclude_files.add(pyfile)


def create_setup_script(opts, pyfiles):
    setup_template_script = os.path.join(os.path.dirname(__file__), "_py2lib_.py.template")
    setup_template_script = os.path.normpath(setup_template_script)
    if os.path.exists(opts.setup_script):
        os.remove(opts.setup_script)
    with open(setup_template_script, "r") as fd:
        template = fd.read()
    files = '", r"'.join(pyfiles)
    n_template = template % (files,)
    with open(opts.setup_script, "w") as fd:
        fd.write(n_template)


def execute_setup_script(opts: Options):
    os.chdir(opts.dir_root)
    cmd = "%s _py2lib_.py build_ext --inplace" % sys.executable
    exit_code, stdout, stderr = shell(cmd, cwd=opts.dir_root)
    # proc = subprocess.Popen(
    #     "%s _py2lib.py build_ext --inplace" % sys.executable,
    #     shell=True,
    #     cwd=opts.dir_root,
    #     text=True,
    #     stderr=subprocess.PIPE,
    #     stdout=subprocess.PIPE,
    # )
    # proc.wait()
    for line in stdout:
        line = line.replace("\r", "").replace("\n", "").strip()
        print(f"[+] \t{line}")
    for line in stderr:
        line = line.replace("\r", "").replace("\n", "").strip()
        print(f"[*] \t{line}")
    return exit_code


def keep_pre_exist_lib(opts: Options):
    for root, dirs, names in os.walk(opts.dir_root):
        for name in names:
            prefix, suffix = os.path.splitext(name)
            if suffix in [".pyd", ".so"]:
                opts.pre_exist_libs.add(os.path.join(root, name))


def cleanup(opts: Options, ext_names=[".pyd", ".so", ".ini", ".cfg", ".yaml", ".txt"]):
    exclude_files = [os.path.join(opts.dir_root, pyfile) for pyfile in opts.exclude_files]
    for root, dirs, names in os.walk(opts.dir_root):
        for name in names:
            if name in ["setup.py", "setup.cfg", "__init__.py"]:
                continue
            abspath = os.path.join(root, name)
            if abspath in opts.pre_exist_libs:
                continue
            if abspath in exclude_files:
                continue
            prefix, suffix = os.path.splitext(name)
            if suffix in ext_names:
                print(f"[+] Delete {abspath}")
                os.remove(abspath)


def compile_projects(dirpath: str):
    opts = Options()
    dirpath = os.path.abspath(os.path.normpath(dirpath))
    if dirpath[-1] == os.path.sep:
        dirpath = dirpath[:-1]
    opts.dir_root = dirpath
    opts.setup_script = os.path.join(opts.dir_root, "_py2lib_.py")

    # 预先保存已经存在 pyd/so文件
    keep_pre_exist_lib(opts)
    # 加载不需要的目录/文件
    load_exclude_options(opts)
    # 获取需要编译的目录
    should_compile_files = get_all_compile_files(opts)

    success = True

    if not isWindows:
        create_setup_script(opts, should_compile_files)
        execute_setup_script(opts)
    else:
        for pyfile in should_compile_files:
            print(f"[+] start compile {pyfile}")
            create_setup_script(opts, [pyfile])
            execute_setup_script(opts)

    for root, dirs, names in os.walk(opts.dir_root):
        for name in names:
            abspath = os.path.join(root, name)
            if abspath in opts.pre_exist_libs:
                continue
            prefix, suffix = os.path.splitext(name)
            if suffix not in [".so", ".pyd"]:
                continue
            parts = name.split(".")
            new_name = ".".join([parts[0], parts[-1]])
            new_abspath = os.path.join(root, new_name)
            print(f"[+] Rename: {new_abspath}")
            os.rename(abspath, new_abspath)

    shutil.rmtree(os.path.join(opts.dir_root, "build"))
    shutil.rmtree(os.path.join(opts.dir_root, "tmp_build"))
    cleanup(opts, ext_names=[".py", ".pyc"])

    return success


def start_compile_all_folder(dirpath):
    # type: (str) -> (bool, None | Exception)
    try:
        r = compile_projects(dirpath)
        return True, None
    except Exception as err:
        return False, err
