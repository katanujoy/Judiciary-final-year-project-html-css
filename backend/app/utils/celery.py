from celery import Celery

celery = Celery(
    'judiciary',
    broker='redis://localhost:6379/0',   # change if using another broker
    backend='redis://localhost:6379/0'
)
