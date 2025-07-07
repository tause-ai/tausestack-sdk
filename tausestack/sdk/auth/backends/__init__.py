# Firebase backend removed - using Supabase instead
# from .firebase_admin import FirebaseAuthBackend
from .supabase_auth import SupabaseAuthBackend, SupabaseVerifiedToken

__all__ = ["SupabaseAuthBackend", "SupabaseVerifiedToken"]
