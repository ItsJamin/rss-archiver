import os

from dotenv import load_dotenv
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


load_dotenv()

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_name="development"):
    app = Flask(__name__)

    app.secret_key = os.environ.get('SECRET_KEY', 'unsafe_default_dev_key')
    app.config.update(
        SQLALCHEMY_DATABASE_URI = 'sqlite:///rss.db'
    )

    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)

    from . import models

    with app.app_context():
        db.create_all()

    # Register blueprints
    from .blueprints.web import web_bp
    app.register_blueprint(web_bp)

    from .blueprints.api import api_bp
    app.register_blueprint(api_bp)

    return app
