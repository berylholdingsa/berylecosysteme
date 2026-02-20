package com.beryl.sentinel.security

import io.ktor.server.application.ApplicationCall
import io.ktor.server.application.createRouteScopedPlugin
import io.ktor.server.application.install
import io.ktor.server.routing.Route

class JwtAuthenticationPluginConfig {
    lateinit var verifier: JwtVerifier
}

val JwtAuthenticationPlugin = createRouteScopedPlugin(
    name = "JwtAuthenticationPlugin",
    createConfiguration = ::JwtAuthenticationPluginConfig
) {
    val verifier = pluginConfig.verifier
    onCall { call ->
        val token = call.request.headers["Authorization"]
            ?.trim()
            ?.takeIf { it.startsWith("Bearer ", ignoreCase = true) }
            ?.substringAfter("Bearer ")
            ?.trim()
            .orEmpty()

        if (token.isEmpty()) {
            throw UnauthorizedException("Authorization bearer token required")
        }

        val principal = runCatching {
            verifier.verifyIdToken(token, checkRevoked = true)
        }.getOrElse {
            throw UnauthorizedException("Unauthorized")
        }
        call.attributes.put(JwtPrincipalKey, principal)
    }
}

fun Route.authenticateJwt(
    verifier: JwtVerifier,
    build: Route.() -> Unit
) {
    install(JwtAuthenticationPlugin) {
        this.verifier = verifier
    }
    build()
}

fun ApplicationCall.jwtPrincipal(): AuthenticatedPrincipal? {
    return if (attributes.contains(JwtPrincipalKey)) {
        attributes[JwtPrincipalKey]
    } else {
        null
    }
}
