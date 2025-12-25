# myproject/celery.py
import os
from celery import Celery

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jaysmetal_backend.settings')

app = Celery('jaysmetal_backend')

# Load task modules from all registered Django app configs
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print('Request: debug_task worked')
    # print(f'Request: {self.request!r}')


@app.task
def update_fabrication_reports():
    """Run daily/hourly to keep reports current"""
    from django.core.management import call_command
    call_command('populate_fab_reports', '--days=7')  # Last 7 days only
