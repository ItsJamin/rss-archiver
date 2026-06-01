import email
import html
import os
from datetime import datetime, timedelta

from flask import Blueprint, Response, current_app
from sqlalchemy import func

from app.models import Article, Feed, db


rss_bp = Blueprint("rss", __name__, url_prefix="/rss")

def _escape_xml(text):
    if not text:
        return ""
    return html.escape(text, quote=True)

def _get_today_range():
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return today_start, today_start + timedelta(days=1)

def _get_week_range():
    today = datetime.utcnow()
    monday = today - timedelta(days=today.weekday())
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    return monday, monday + timedelta(days=7)

def _generate_rss_feed(articles, title, description, base_url, feed_path):
    rss_items = []
    for article in articles:
        pub_date = article.publish_date or article.fetched_at
        pub_date_rfc2822 = email.utils.format_datetime(pub_date)
        guid = article.guid or article.url

        try:
            with open(article.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            content = ""

        title_escaped = _escape_xml(article.title or "[No Title]")
        link = _escape_xml(article.url)
        guid_escaped = _escape_xml(guid)
        description = _escape_xml(content)
        author = _escape_xml(article.author) if article.author else None

        item = f'    <item>\n' \
               f'      <title>{title_escaped}</title>\n' \
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
    <title>{title}</title>
    <description>{description}</description>
    <link>{base_url}</link>
    <language>en-us</language>
    <pubDate>{now_rfc2822}</pubDate>
    <lastBuildDate>{now_rfc2822}</lastBuildDate>
    <ttl>60</ttl>
    <generator>RSS Archiver</generator>
    <atom:link href="{base_url}{feed_path}" rel="self" type="application/rss+xml"/>
{items_xml}
  </channel>
</rss>'''

    return rss_xml

def _get_base_url():
    base_url = current_app.config.get('SERVER_NAME', 'localhost:5431')
    if not base_url.startswith(('http://', 'https://')):
        base_url = f'http://{base_url}'
    return base_url

@rss_bp.route("/today")
def today_rss_feed():
    start, end = _get_today_range()
    articles = Article.query.filter(
        Article.publish_date >= start,
        Article.publish_date < end
    ).order_by(func.coalesce(Article.publish_date, Article.fetched_at).desc()).all()

    base_url = _get_base_url()
    rss_xml = _generate_rss_feed(
        articles,
        "RSS Archiver - Today's News",
        "All articles fetched today from your RSS Archiver",
        base_url,
        "/rss/today"
    )
    return Response(rss_xml, mimetype='application/rss+xml')

@rss_bp.route("/week")
def week_rss_feed():
    start, end = _get_week_range()
    articles = Article.query.filter(
        Article.publish_date >= start,
        Article.publish_date < end
    ).order_by(func.coalesce(Article.publish_date, Article.fetched_at).desc()).all()

    base_url = _get_base_url()
    rss_xml = _generate_rss_feed(
        articles,
        "RSS Archiver - This Week's News",
        "All articles fetched this week from your RSS Archiver",
        base_url,
        "/rss/week"
    )
    return Response(rss_xml, mimetype='application/rss+xml')
