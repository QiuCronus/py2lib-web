from django.db import models

# Create your models here.




class Account(models.Model):
    username = models.CharField(max_length=128, unique=True)
    password = models.CharField(max_length=256)

    def __str__(self):
        return self.username

    class Meta:
        db_table = "accounts"
        verbose_name = "用户"
        verbose_name_plural = "用户"


class TaskRecord(models.Model):

    PENDING = 0
    CHECKING = 1
    CHECKED = 2
    COMPILING = 3
    COMPILED = 4
    WHEELING = 5
    SUCCESS = 6
    ERR_CHECKING = 7
    ERR_COMPILING = 8
    ERR_WHEELING = 9

    TASK_STATUS_CHOICES = (
        (PENDING, "待处理"),

        (CHECKING, "校验中"),
        (COMPILING, "编译中"),
        (WHEELING, "打包中"),

        (SUCCESS, "完成"),

        (CHECKED, "校验完成"),
        (COMPILED, "编译完成"),

        (ERR_CHECKING, "校验失败"),
        (ERR_COMPILING, "编译失败"),
        (ERR_WHEELING, "打包失败"),
    )

    id = models.AutoField(primary_key=True)
    task_id = models.CharField(max_length=64, unique=True)
    filename = models.CharField(max_length=256)
    local_path = models.TextField("localpath", null=True)
    status = models.IntegerField(max_length=2, choices=TASK_STATUS_CHOICES, default=PENDING)
    # status = models.IntegerField("状态", default=0)
    whl = models.TextField("whl", null=True, blank=True)
    created_at = models.DateTimeField("created_at", auto_now_add=True)
    modified_at = models.DateTimeField("modified_at", auto_now=True)

    err_msg = models.TextField("error", null=True, blank=True)

    user = models.ForeignKey(to="Account", on_delete=models.CASCADE)

    def __str__(self):
        return self.task_id

    class Meta:
        db_table = "builder_tasks"
        verbose_name = "任务"
        verbose_name_plural = "任务"