import os

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app.models import Article, Feed, db


web_bp = Blueprint("web", __name__, template_folder="templates/web/")

@web_bp.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        url = request.form.get("url", "").strip()
        if not url:
            feeds = Feed.query.order_by(Feed.title).all()
            return render_template("home.html", feeds=feeds, error="URL is required")

        if Feed.query.filter_by(url=url).first():
            feeds = Feed.query.order_by(Feed.title).all()
            return render_template("home.html", feeds=feeds, error="Feed with this URL already registered")

        new_feed = Feed(
            url=url,
            title=request.form.get("title", "").strip(),
            description=request.form.get("description", "").strip()
        )
        db.session.add(new_feed)
        db.session.commit()
        flash("Feed successfully registered!", "success")
        return redirect(url_for("web.home"))

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
