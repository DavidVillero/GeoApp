import os

from flask import Flask

from .celery_utils import start_celery

PKG_NAME = os.path.dirname(os.path.realpath(__file__)).split("/")[-1]


def create_app(app_name=PKG_NAME, **kwargs):
    app = Flask(app_name)
    if kwargs.get("celery"):
        start_celery(kwargs.get("celery"), app)
    from app.routes import bp
    app.register_blueprint(bp)
    return app
