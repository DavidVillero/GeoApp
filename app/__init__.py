from celery import Celery

def make_worker(app_name=__name__):
    """This fucntion will create my celery worker with a redis backend

    Args:
        app_name ([type], optional): [description]. Defaults to __name__.

    Returns:
        [type]: [description]
    """
    backend = "redis://redis:6379/0"
    broker = "redis://redis:6379/1"
    return Celery(app_name, backend=backend, broker=broker)

celery = make_worker()
