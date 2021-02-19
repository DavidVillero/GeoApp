def start_celery(celery, app):
    """This fucntion will initialize my celery worker config

    Args:
        celery ([type]): [description]
        app ([type]): [description]

    Returns:
        [type]: [description]
    """
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
