import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'household_electricity_dashboard.settings')

app = Celery('household_electricity_dashboard')

# Load configuration from Django settings (prefix 'CELERY_') so development
# settings like CELERY_TASK_ALWAYS_EAGER are respected without modifying this file.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Use a default broker; override with CELERY_BROKER_URL in settings or environment
app.conf.broker_url = os.environ.get('CELERY_BROKER_URL', app.conf.get('broker_url', 'redis://localhost:6379/0'))
app.conf.result_backend = os.environ.get('CELERY_RESULT_BACKEND', app.conf.get('result_backend', app.conf.broker_url))

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
