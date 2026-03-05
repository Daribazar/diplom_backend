"""Custom application exceptions."""


class AppException(Exception):
    """Base application exception."""
    
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundException(AppException):
    """Resource not found exception."""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class UnauthorizedException(AppException):
    """Unauthorized access exception."""
    
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)


class ForbiddenException(AppException):
    """Forbidden access exception."""
    
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, status_code=403)


class ValidationException(AppException):
    """Validation error exception."""
    
    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status_code=422)


class ConflictException(AppException):
    """Resource conflict exception."""
    
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, status_code=409)


# Auth-specific exceptions
class DuplicateEmailError(AppException):
    """Email already registered."""
    
    def __init__(self, message: str = "Email already registered"):
        super().__init__(message, status_code=409)


class InvalidCredentialsError(AppException):
    """Invalid login credentials."""
    
    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(message, status_code=401)


class UnauthorizedError(AppException):
    """Unauthorized access."""
    
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)


class NotFoundError(AppException):
    """Resource not found."""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class DuplicateError(AppException):
    """Duplicate resource error."""
    
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message, status_code=409)
