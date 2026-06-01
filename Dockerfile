FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=run.py
ENV FLASK_ENV=development

RUN mkdir -p data/archives
RUN mkdir -p instance/

EXPOSE 5431

CMD ["flask", "run", "--host=0.0.0.0", "--port=5431"]