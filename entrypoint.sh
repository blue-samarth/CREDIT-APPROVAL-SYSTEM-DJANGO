#!/bin/bash
set -e

echo "Waiting for database..."
while ! python -c "
import os
import sys
try:
    if os.getenv('DATABASE_URL', '').startswith('postgresql'):
        import psycopg2
        from urllib.parse import urlparse
        url = urlparse(os.getenv('DATABASE_URL'))
        conn = psycopg2.connect(
            dbname=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
        conn.close()
        sys.exit(0)
    else:
        sys.exit(0)
except Exception as e:
    sys.exit(1)
" 2>/dev/null; do
  echo "Database not ready - waiting..."
  sleep 2
done

echo "Database ready!"

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput || true

echo "Starting application..."
exec "$@"
