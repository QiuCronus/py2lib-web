import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "py2lib.settings")

app = Celery("py2lib")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True)
def debug_celery_activate(self):
    print(f"Request: {self.request!r}")
