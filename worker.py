from app import celery
from app.controller import create_app
from app.celery_utils import start_celery
app = create_app()
start_celery(celery, app)