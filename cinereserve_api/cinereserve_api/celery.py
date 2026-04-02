import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cinereserve_api.settings')

app = Celery('cinereserve_api')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.update(
    timezone='America/Sao_Paulo',
    enable_utc=True
)