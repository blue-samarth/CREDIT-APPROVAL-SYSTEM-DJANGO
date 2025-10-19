#!/usr/bin/env python
"""Quick test script to verify Celery setup."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()


def test_all():
    print("🧪 Testing Celery Setup\n")
    
    # Test 1: Redis
    try:
        from django.conf import settings
        import redis
        r = redis.from_url(settings.CELERY_BROKER_URL)
        r.ping()
        print("✅ Redis connection")
    except:
        print("❌ Redis connection - Start with: redis-server")
        return False
    
    # Test 2: Celery
    try:
        from config.celery import app
        print("✅ Celery import")
    except Exception as e:
        print(f"❌ Celery import failed: {e}")
        return False
    
    # Test 3: Tasks
    try:
        from config.celery import app
        tasks = [t for t in app.tasks.keys() if t.startswith('core.')]
        print(f"✅ Task discovery ({len(tasks)} tasks found)")
    except Exception as e:
        print(f"❌ Task discovery failed: {e}")
        return False
    
    # Test 4: Business logic
    try:
        from core.utils.data_ingestion import ingest_customers_from_excel
        print("✅ Business logic imports")
    except Exception as e:
        print(f"❌ Business logic failed: {e}")
        return False
    
    # Test 5: Data files
    if os.path.exists('data/customer_data.xlsx') and os.path.exists('data/loan_data.xlsx'):
        print("✅ Data files exist")
    else:
        print("❌ Data files missing")
        return False
    
    print("\n🎉 All checks passed!\n")
    print("Start worker: uv run celery -A config worker --loglevel=info")
    print("Run command:  uv run python manage.py ingest_data")
    return True


if __name__ == '__main__':
    sys.exit(0 if test_all() else 1)