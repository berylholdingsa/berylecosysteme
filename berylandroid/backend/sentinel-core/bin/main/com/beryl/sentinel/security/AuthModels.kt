package com.beryl.sentinel.security

import io.ktor.util.AttributeKey

data class AuthenticatedPrincipal(
    val uid: String,
    val claims: Map<String, Any?> = emptyMap()
)

class UnauthorizedException(message: String) : RuntimeException(message)

val JwtPrincipalKey = AttributeKey<AuthenticatedPrincipal>("jwt_principal")
