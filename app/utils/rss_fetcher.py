import hashlib
import os
from datetime import datetime

import feedparser

from app.models import Article, Feed, db


def fetch_and_store_feed(feed_id):
    from flask import current_app

    with current_app.app_context():
        feed = Feed.query.get(feed_id)
        if not feed or not feed.is_active:
            current_app.logger.warning(f"Feed {feed_id} not found or inactive")
            return False

        try:
            parsed_feed = feedparser.parse(feed.url)
            current_app.logger.info(f"Fetched feed {feed_id}: {len(parsed_feed.entries)} entries")

            archive_dir = os.path.join("data", "archives", str(feed_id))
            os.makedirs(archive_dir, exist_ok=True)

            for entry in parsed_feed.entries:
                url = entry.get("link", "")
                if not url:
                    continue

                guid = entry.get("id", "") or entry.get("guid", "")
                title = entry.get("title", "[No Title]")

                publish_date = None
                if hasattr(entry, "published_parsed"):
                    publish_date = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, "updated_parsed"):
                    publish_date = datetime(*entry.updated_parsed[:6])

                author = ""
                if hasattr(entry, "author"):
                    author = entry.author
                elif hasattr(entry, "author_detail"):
                    ad = entry.author_detail
                    if isinstance(ad, dict):
                        author = ad.get("name", "")
                    elif isinstance(ad, list) and ad:
                        author = ad[0].get("name", "")

                # (content > description)
                content = ""
                if hasattr(entry, "content"):
                    if isinstance(entry.content, list) and entry.content:
                        content = entry.content[0].get("value", "")
                    elif isinstance(entry.content, str):
                        content = entry.content
                if not content:
                    content = entry.get("description", "")

                if not content:
                    continue

                content_hash = hashlib.sha256(content.encode()).hexdigest()

                # check if article exists
                article = Article.query.filter_by(feed_id=feed_id, url=url).first()

                if article:
                    if article.content_hash == content_hash:
                        continue
                    else:
                        article.version += 1
                        article.content_hash = content_hash
                        article.title = title
                        article.publish_date = publish_date
                        article.author = author
                        article.fetched_at = datetime.utcnow()
                else:
                    article = Article(
                        feed_id=feed_id,
                        url=url,
                        guid=guid,
                        title=title,
                        publish_date=publish_date,
                        author=author,
                        content_hash=content_hash,
                        version=1,
                        fetched_at=datetime.utcnow()
                    )
                    db.session.add(article)

                file_name = f"{content_hash}_{article.version}.html"
                file_path = os.path.join(archive_dir, file_name)
                article.file_path = file_path

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

                db.session.commit()

            return True

        except Exception as e:
            current_app.logger.error(f"Error fetching feed {feed_id}: {str(e)}")
            db.session.rollback()
            return False

def fetch_all_feeds():
    from flask import current_app
    with current_app.app_context():
        feeds = Feed.query.filter_by(is_active=True).all()
        for feed in feeds:
            fetch_and_store_feed(feed.id)
