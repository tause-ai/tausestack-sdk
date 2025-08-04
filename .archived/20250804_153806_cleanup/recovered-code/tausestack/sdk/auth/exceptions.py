# Tausestack SDK - Auth Exceptions

class AuthException(Exception):
    """Base exception para errores de autenticación."""
    pass

class InvalidTokenException(AuthException):
    """Lanzada cuando un token es inválido o ha expirado."""
    pass

class UserNotFoundException(AuthException):
    """Lanzada cuando no se encuentra un usuario."""
    pass

class InsufficientPermissionsException(AuthException):
    """Lanzada cuando un usuario no tiene los permisos necesarios."""
    pass

class AccountDisabledException(AuthException):
    """Lanzada cuando la cuenta del usuario está deshabilitada."""
    pass
