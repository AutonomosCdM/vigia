"""
Módulo de interfaz con base de datos para LPP-Detect.

Este módulo proporciona clientes y utilidades para interactuar con
la base de datos de LPP-Detect.
"""

from .supabase_client import SupabaseClientRefactored as SupabaseClient

__all__ = ['SupabaseClient']
