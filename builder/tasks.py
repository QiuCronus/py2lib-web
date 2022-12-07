import time
import zipfile
import os

from django.conf import settings

from py2lib import celery_app

from .models import TaskRecord

@celery_app.task
def verfiy_upload_files(task_id):
    task = TaskRecord.objects.get(task_id=task_id)
    task.status = TaskRecord.CHECKING
    task.save()

    workspace = os.path.join(settings.DIR_TEMP, task.task_id)
    os.makedirs(workspace, exist_ok=True)

    with zipfile.ZipFile(task.local_path, "r") as zf:
        zf.extractall(workspace)

    cfg = os.path.join(workspace, "py2lib.cfg")
    if not os.path.exists(cfg):
        task.err_msg = "文件根目录没有 py2lib.cfg 文件"
        task.status = TaskRecord.ERR_CHECKING
        task.save()
        return

    pysetup = os.path.join(workspace, "setup.py")
    if not os.path.exists(pysetup):
        task.err_msg = "文件根目录没有 setup.py 文件"
        task.status = TaskRecord.ERR_CHECKING
        task.save()
        return

    task.staus = TaskRecord.CHECKED
    task.save()
    return task_id

@celery_app.task
def compile_py_to_lib(task_id):
    if not task_id:
        return

    task = TaskRecord.objects.get(task_id=task_id)
    if task.status != TaskRecord.CHECKED:
        raise RuntimeError("task should be CHECKED before compile.")

    task.status = TaskRecord.COMPILING
    task.save()

    print("compile_py_to_lib ...")
    time.sleep(10)

    task.status = TaskRecord.COMPILED
    return task_id



@celery_app.task
def build_py_to_wheel(task_id):
    if not task_id:
        return

    task = TaskRecord.objects.get(task_id=task_id)
    if task.status != TaskRecord.COMPILED:
        raise RuntimeError("task should be COMPILED before packing.")

    task.status = TaskRecord.WHEELING
    task.save()

    print("build_py_to_wheel ...")
    time.sleep(10)

    task.status = TaskRecord.SUCCESS
    task.save()
    return task_id