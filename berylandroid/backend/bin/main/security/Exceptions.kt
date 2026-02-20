class UnauthorizedException(message: String) : RuntimeException(message)
class ValidationException(message: String) : RuntimeException(message)
class RateLimitException(message: String) : RuntimeException(message)
