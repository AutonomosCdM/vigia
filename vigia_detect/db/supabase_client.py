"""
Supabase Client - Compatibility Import

Provides backward compatibility for supabase_client imports.
"""

# Import from the refactored version
from .supabase_client_refactored import SupabaseClient

__all__ = ['SupabaseClient']