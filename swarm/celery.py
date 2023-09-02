import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vw_storages.settings')

app = Celery('swarm')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
