A simple archive-tool to aggregate and longterm-save rss news.

Features:
- scheduled fetching of rss feed
- longterm saving in db/as files
- aggregates rss feed for today/week
- simple web interface

# Install

```
git clone https://github.com/ItsJamin/rss-archiver
cp .env.example .env
```

edit .env if needed to change e.g. the fetch-schedule

Example `docker-compose.yml`:
```
services:
  web:
    build: .
    ports:
      - "5431:5431"
    volumes:
      - ./:/app/
    environment:
      - FLASK_APP=run.py
      - FLASK_ENV=development
    restart: unless-stopped
```

```
docker compose build
docker compose up -d
```