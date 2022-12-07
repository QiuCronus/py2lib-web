import os
import uuid

from django.shortcuts import render, redirect
from django.conf import settings

from .tasks import compile_py_to_lib, build_py_to_wheel, verfiy_upload_files
from .forms import AccountForm
from .models import Account, TaskRecord


def index(request):
    # 主页
    all_tasks = []
    if request.session.get("is_login", None):
        # 已经登录的，显示对应的任务列表
        login_user_id = request.session.get("user_id")
        all_tasks = TaskRecord.objects.filter(user=login_user_id).all()
    return render(request, "login/index.html", locals())


def upload_file(request):
    if not request.session.get("is_login", None):
        return render(request, "login/login.html", locals())

    if request.method == "POST":
        login_user_name = request.session.get("user_name")
        login_user = Account.objects.get(username=login_user_name)

        upload_file_stream = request.FILES.get("file")
        task_id = uuid.uuid4().hex
        store_received_dir = os.path.join(settings.DIR_UPLOAD, login_user_name, task_id)
        os.makedirs(store_received_dir, exist_ok=True)
        filepath = os.path.join(store_received_dir, upload_file_stream.name)
        with open(filepath, "wb") as fd:
            for chunk in upload_file_stream.chunks():
                fd.write(chunk)

        TaskRecord.objects.create(
            task_id=task_id, filename=upload_file_stream.name,
            local_path=filepath, status=TaskRecord.PENDING,
            whl="", user=login_user
        )
        verfiy_upload_files.apply_async((task_id,), link=[compile_py_to_lib.s(), build_py_to_wheel.s()])
    return redirect("/index", locals())


def check_login_user(request, login_form):
    if login_form.is_valid():
        username = login_form.cleaned_data["username"]
        password = login_form.cleaned_data["password"]
        try:
            account = Account.objects.get(username=username)
            if account.password == password:
                request.session["is_login"] = True
                request.session["user"] = account
                request.session["user_name"] = account.username
                return True, None
            else:
                return False, "密码错误"
        except Exception as err:
            return False, "用户不存在"


def login(request):
    if request.session.get("is_login", None):
        return redirect("/index")

    if request.method == "POST":
        login_form = AccountForm(request.POST)
        message = "请检查填写的内容！"
        if login_form.is_valid():
            username = login_form.cleaned_data["username"]
            password = login_form.cleaned_data["password"]
            try:
                account = Account.objects.get(username=username)
                if account.password == password:
                    request.session["is_login"] = True
                    request.session["user_id"] = account.id
                    request.session["user_name"] = account.username
                    request.session.set_expiry(600)
                    return redirect("/index")

                message = "密码错误"
            except Exception as err:
                message = "用户不存在"
            return render(request, "login/login.html", locals())

    login_form = AccountForm()
    return render(request, "login/login.html", locals())


def logout(request):
    if not request.session.get("is_login", None):
        return redirect("/index/")
    request.session.flush()
    return redirect("/index/")
