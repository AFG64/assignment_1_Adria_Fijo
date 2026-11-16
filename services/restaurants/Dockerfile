FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY services/restaurants/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home picky
COPY service_runtime/ /app/service_runtime/
COPY services/restaurants/app.py /app/app.py
COPY services/restaurants/migrations/ /app/migrations/
ARG VERSION=local
ENV VERSION=$VERSION
USER 10001
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=8s --start-period=120s --retries=6 CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.getenv('PORT', '8000') + '/health', timeout=7)"
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 1 --timeout 120 --access-logfile - app:app"]
