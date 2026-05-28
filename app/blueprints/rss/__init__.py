import email
import html
import os
from datetime import datetime, timedelta

from flask import Blueprint, Response, current_app

from app.models import Article, Feed, db


rss_bp = Blueprint("rss", __name__, url_prefix="/rss")

def _escape_xml(text):
    """Escape XML-Sonderzeichen (z. B. &, <, >)."""
    if not text:
        return ""
    return html.escape(text, quote=True)


@rss_bp.route("/today")
def today_rss_feed():
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_start = today_start + timedelta(days=1)

    articles = Article.query.filter(
        Article.fetched_at >= today_start,
        Article.fetched_at < tomorrow_start
    ).order_by(Article.fetched_at.desc()).all()

    base_url = current_app.config.get('SERVER_NAME', 'localhost:5431')
    if not base_url.startswith(('http://', 'https://')):
        base_url = f'http://{base_url}'

    rss_items = []
    for article in articles:
        pub_date = article.publish_date or article.fetched_at
        pub_date_rfc2822 = email.utils.format_datetime(pub_date)

        # GUID (fallback: URL)
        guid = article.guid or article.url

        try:
            with open(article.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            content = ""

        # XML-Escaping
        title = _escape_xml(article.title or "[No Title]")
        link = _escape_xml(article.url)
        guid_escaped = _escape_xml(guid)
        description = _escape_xml(content)
        author = _escape_xml(article.author) if article.author else None

        item = f'    <item>\n' \
               f'      <title>{title}</title>\n' \
               f'      <link>{link}</link>\n' \
               f'      <guid>{guid_escaped}</guid>\n' \
               f'      <pubDate>{pub_date_rfc2822}</pubDate>\n' \
               f'      <description>{description}</description>\n'
        if author:
            item += f'      <author>{author}</author>\n'
        item += '    </item>'
        rss_items.append(item)

    items_xml = "\n".join(rss_items)

    now = datetime.utcnow()
    now_rfc2822 = email.utils.format_datetime(now)

    rss_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>RSS Archiver - Today's News</title>
    <description>All articles fetched today from your RSS Archiver</description>
    <link>{base_url}</link>
    <language>en-us</language>
    <pubDate>{now_rfc2822}</pubDate>
    <lastBuildDate>{now_rfc2822}</lastBuildDate>
    <ttl>60</ttl>
    <generator>RSS Archiver</generator>
    <atom:link href="{base_url}/today/rss" rel="self" type="application/rss+xml"/>
{items_xml}
  </channel>
</rss>'''

    return Response(
        rss_xml,
        mimetype='application/rss+xml'
    )
