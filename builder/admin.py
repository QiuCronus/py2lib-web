from django.contrib import admin

# Register your models here.
from .models import Account, TaskRecord


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("username", "password")


@admin.register(TaskRecord)
class TaskRecordAdmin(admin.ModelAdmin):
    list_display = ("task_id", "filename", "status", "whl")