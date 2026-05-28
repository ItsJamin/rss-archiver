import atexit
import os

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


load_dotenv()

db = SQLAlchemy()
migrate = Migrate()


def init_scheduler(app, hours, minutes):
    def fetch_job():
        with app.app_context():
            from .utils.rss_fetcher import fetch_all_feeds
            fetch_all_feeds()

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=fetch_job,
        trigger="interval",
        hours=int(hours),
        minutes=int(minutes),
        id="fetch_feeds",
        replace_existing=True
    )
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())

def create_app(config_name="development"):
    app = Flask(__name__)

    app.secret_key = os.environ.get('SECRET_KEY', 'unsafe_default_dev_key')
    app.config.update(
        SQLALCHEMY_DATABASE_URI = 'sqlite:///rss.db'
    )

    app.config["SERVER_NAME"] = os.environ.get('SERVER_NAME', "localhost:54321")

    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)

    from . import models

    with app.app_context():
        db.create_all()
        init_scheduler(app, hours=os.environ.get('S_HOURS', 3), minutes=os.environ.get('S_MINUTES', 0))

    # Register blueprints
    from .blueprints.web import web_bp
    app.register_blueprint(web_bp)

    from .blueprints.api import api_bp
    app.register_blueprint(api_bp)

    from .blueprints.rss import rss_bp
    app.register_blueprint(rss_bp)

    return app
