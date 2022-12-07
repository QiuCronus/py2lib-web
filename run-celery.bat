@echo off

celery -A py2lib worker -P solo -l info