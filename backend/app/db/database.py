"""Supabase database client initialization"""

from app.config import settings

supabase = None

if settings.supabase_url and settings.supabase_key:
    from supabase import create_client
    supabase = create_client(settings.supabase_url, settings.supabase_key)
