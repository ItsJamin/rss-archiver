import os

from flask import Blueprint, jsonify, request
from werkzeug.exceptions import BadRequest, NotFound

from app.models import Article, Feed, db


api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route('/feeds', methods=['POST'])
def register_feed():
    """Register a new RSS feed."""
    data = request.get_json()
    if not data:
        raise BadRequest("Request body must be JSON")

    url = data.get('url')
    if not url:
        raise BadRequest("URL is required")

    if Feed.query.filter_by(url=url).first():
        raise BadRequest(f"Feed with URL '{url}' already registered")

    new_feed = Feed(
        url=url,
        title=data.get('title', ''),
        description=data.get('description', '')
    )
    db.session.add(new_feed)
    db.session.commit()

    return jsonify({
        'id': new_feed.id,
        'url': new_feed.url,
        'title': new_feed.title,
        'description': new_feed.description,
        'created_at': new_feed.created_at.isoformat(),
        'is_active': new_feed.is_active
    }), 201

@api_bp.route('/feeds', methods=['GET'])
def list_feeds():
    """List all registered feeds."""
    feeds = Feed.query.all()
    return jsonify([{
        'id': feed.id,
        'url': feed.url,
        'title': feed.title,
        'description': feed.description,
        'created_at': feed.created_at.isoformat(),
        'is_active': feed.is_active,
        'article_count': len(feed.articles)
    } for feed in feeds])

@api_bp.route('/feeds/<int:feed_id>', methods=['DELETE'])
def unregister_feed(feed_id):
    """Unregister a feed and delete its articles and files."""
    feed = Feed.query.get(feed_id)
    if not feed:
        raise NotFound(f"Feed with ID {feed_id} not found")

    for article in feed.articles[:]:
        try:
            if os.path.exists(article.file_path):
                os.remove(article.file_path)
        except Exception:
            pass
        db.session.delete(article)

    db.session.delete(feed)
    db.session.commit()

    return jsonify({'message': f'Feed {feed_id} and its articles deleted'}), 200

@api_bp.route('/feeds/<int:feed_id>/articles', methods=['GET'])
def get_feed_articles(feed_id):
    """Get all archived articles from a feed."""
    feed = Feed.query.get(feed_id)
    if not feed:
        raise NotFound(f"Feed with ID {feed_id} not found")

    articles = Article.query.filter_by(feed_id=feed_id).order_by(Article.fetched_at.desc()).all()
    return jsonify([{
        'id': article.id,
        'feed_id': article.feed_id,
        'url': article.url,
        'guid': article.guid,
        'title': article.title,
        'publish_date': article.publish_date.isoformat() if article.publish_date else None,
        'author': article.author,
        'content_hash': article.content_hash,
        'file_path': article.file_path,
        'fetched_at': article.fetched_at.isoformat(),
        'version': article.version
    } for article in articles])

@api_bp.route('/articles/<int:article_id>/content', methods=['GET'])
def get_article_content(article_id):
    """Get the content of a specific article."""
    article = Article.query.get(article_id)
    if not article:
        raise NotFound(f"Article with ID {article_id} not found")

    try:
        with open(article.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({
            'id': article.id,
            'content': content
        })
    except FileNotFoundError:
        raise NotFound(f"Content file for article {article_id} not found")
    except Exception as e:
        raise BadRequest(f"Error reading content file: {str(e)}")

@api_bp.route('/feeds/<int:feed_id>/fetch', methods=['POST'])
def fetch_feed(feed_id):
    from app.utils.rss_fetcher import fetch_and_store_feed
    feed = Feed.query.get(feed_id)
    if not feed:
        raise NotFound(f"Feed with ID {feed_id} not found")

    success = fetch_and_store_feed(feed_id)
    if success:
        return jsonify({'message': f'Feed {feed_id} fetched successfully'}), 200
    else:
        return jsonify({'error': f'Failed to fetch feed {feed_id}'}), 400

@api_bp.route('/feeds/fetch-all', methods=['GET','POST'])
def fetch_all_feeds():
    from app.utils.rss_fetcher import fetch_all_feeds
    fetch_all_feeds()
    return jsonify({'message': 'All active feeds fetched successfully'}), 200
