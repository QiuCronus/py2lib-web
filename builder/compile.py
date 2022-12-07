import os
import sys
import shutil
import platform
import subprocess
from configparser import ConfigParser

from distutils.core import setup, Extension
from Cython.Build import cythonize


def is_windowns():
	return platform.platform().lower().startswith("win")


def rm(path):
	if os.path.exists(path):
		os.remove(path)


def compile2lib(filepath):
	dirpath, filename = os.path.split(filepath)
	os.chdir(dirpath)
	module = os.path.splitext(filename)[0]

	if is_windowns():
		src = module + ".cp37-win_amd64.pyd"
		dst = module + ".pyd"
	else:
		src = module + ".cpython-37m-x86_64-linux-gnu.so"
		dst = module + ".so"
	rm(src)
	rm(dst)
	extensions = [Extension(module, [filename])]
	setup(name=module, ext_modules=cythonize(extensions, language_level=3), script_args=["build_ext", "--inplace"])

	os.rename(src, dst)
	for ext in ("c", "pyc", "py"):
		file = f"{module}.{ext}"
		os.path.isfile(file) and os.remove(file)
	if not is_windowns():
		proc = subprocess.Popen(f"strip {dst}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		proc.wait()


def clean_build(path):
	build_paths = []
	for root, dirs, files in os.walk(path):
		if dirs:
			if "build" in dirs:
				build_paths.append(os.path.join(root, "build"))

	for build_path in build_paths:
		shutil.rmtree(build_path)


def load_exclude_options(dirpath, cfg):
	exclude_dirs = cfg.get("options", "exclude_dirs", "")
	exclude_dirs = [e.strip() for e in exclude_dirs.split("\n") if e.strip()]
	exclude_dirs = [os.path.abspath(os.path.normpath(os.path.join(dirpath, v))) for v in exclude_dirs]

	exclude_files = cfg.get("options", "exclude_files", "")
	exclude_files = [e.strip() for e in exclude_files.split("\n") if e.strip()]
	exclude_files = [os.path.abspath(os.path.normpath(os.path.join(dirpath, v))) for v in exclude_files]

	return exclude_dirs, exclude_files


def is_exclude(filepath, exc_dirs, exc_files):
	if filepath in exc_files:
		return True

	for exc_dir in exc_dirs:
		if exc_dir in filepath:
			return True
	return False


def convert_py_to_lib(dirpath):
	dirpath = os.path.abspath(os.path.normpath(dirpath))

	should_exclude_dirs, should_exclude_files = [], []

	cfg_path = os.path.join(dirpath, "py2lib.cfg")
	if os.path.exists(cfg_path):
		cfg = ConfigParser()
		cfg.read(cfg_path)
		should_exclude_dirs, should_exclude_files = load_exclude_options(dirpath, cfg)

	try:
		for root, _, names in os.walk(dirpath, topdown=False):
			for name in names:
				if not name.endswith(".py"):
					continue
				if name in ["setup.py", "__init__.py"]:
					continue
				abspath = os.path.join(root, name)
				if is_exclude(abspath, should_exclude_dirs, should_exclude_files):
					continue

				compile2lib(abspath)
		return True, None
	except Exception as err:
		return False, err
	finally:
		clean_build(dirpath)
