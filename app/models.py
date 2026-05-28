from datetime import datetime

from . import db


class Feed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), unique=True, nullable=False)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    articles = db.relationship("Article", backref="feed", lazy=True)

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    feed_id = db.Column(db.Integer, db.ForeignKey("feed.id"), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    guid = db.Column(db.String(500)) # do we need this?
    title = db.Column(db.String(500))
    publish_date = db.Column(db.DateTime)
    author = db.Column(db.String(200))
    content_hash = db.Column(db.String(64), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    fetched_at = db.Column(db.DateTime, default=datetime.utcnow)
    version = db.Column(db.Integer, default=1)

    # Unique constraint: One article per feed+URL
    __table_args__ = (db.UniqueConstraint("feed_id", "url", name="unique_article_per_feed"),)
