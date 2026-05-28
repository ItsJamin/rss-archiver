import os

from flask import Blueprint, abort, render_template

from app.models import Article, Feed


web_bp = Blueprint("web", __name__, template_folder="templates/web/")

@web_bp.route("/")
def home():
    feeds = Feed.query.order_by(Feed.title).all()
    return render_template("home.html", feeds=feeds)

@web_bp.route("/feeds/<int:feed_id>")
def feed_detail(feed_id):
    feed = Feed.query.get(feed_id)
    if not feed:
        abort(404)
    articles = Article.query.filter_by(feed_id=feed_id).order_by(Article.publish_date.desc()).all()
    return render_template("feed.html", feed=feed, articles=articles)

@web_bp.route("/articles/<int:article_id>")
def article_detail(article_id):
    article = Article.query.get(article_id)
    if not article:
        abort(404)
    try:
        with open(article.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        content = "<p><em>Content file not found.</em></p>"
    return render_template("article.html", article=article, content=content)
