import os
import zipfile

from django.conf import settings

from py2lib import celery_app
from .compile import start_compile_all_folder
from .models import TaskRecord
from .wheel import bdist_wheel


@celery_app.task
def verfiy_upload_files(task_id):
    task = TaskRecord.objects.get(task_id=task_id)
    task.status = TaskRecord.CHECKING
    task.save()

    workspace = os.path.join(settings.DIR_TEMP, task.task_id)
    os.makedirs(workspace, exist_ok=True)

    with zipfile.ZipFile(task.local_path, "r") as zf:
        zf.extractall(workspace)

    pysetup = os.path.join(workspace, "setup.py")
    if not os.path.exists(pysetup):
        task.err_msg = "文件根目录没有 setup.py 文件"
        task.status = TaskRecord.ERR_CHECKING
        task.save()
        return

    task.status = TaskRecord.CHECKED
    task.save()
    return task_id


@celery_app.task
def compile_py_to_lib(task_id):
    if not task_id:
        return

    task = TaskRecord.objects.get(task_id=task_id)
    if task.status != TaskRecord.CHECKED:
        # raise RuntimeError("task should be CHECKED before compile.")
        return

    task.status = TaskRecord.COMPILING
    task.save()

    workspace = os.path.join(settings.DIR_TEMP, task.task_id)
    try:
        r, err_or_none = start_compile_all_folder(workspace)
        if r:
            task.status = TaskRecord.COMPILED
        else:
            task.status = TaskRecord.ERR_COMPILING
            task.err_msg = str(err_or_none)
    except Exception as err:
        task.status = TaskRecord.ERR_COMPILING
        task.err_msg = str(err)
    finally:
        task.save()

    return task_id


@celery_app.task
def build_py_to_wheel(task_id):
    if not task_id:
        return

    task = TaskRecord.objects.get(task_id=task_id)
    if task.status != TaskRecord.COMPILED:
        return

    task.status = TaskRecord.WHEELING
    task.save()

    workspace = os.path.join(settings.DIR_TEMP, task.task_id)
    try:
        r, err_or_path = bdist_wheel(workspace)
        if r:
            task.status = TaskRecord.SUCCESS
            task.whl = err_or_path
        else:
            task.status = TaskRecord.ERR_WHEELING
            task.err_msg = str(err_or_path)
    except Exception as err:
        task.status = TaskRecord.ERR_WHEELING
        task.err_msg = str(err)
    finally:
        task.save()

    return task_id
