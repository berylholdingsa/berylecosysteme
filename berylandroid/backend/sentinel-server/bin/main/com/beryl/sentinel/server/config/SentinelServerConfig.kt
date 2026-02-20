package com.beryl.sentinel.server.config

data class JwtConfig(
    val issuer: String,
    val audience: String,
    val realm: String
)

object SentinelServerConfig {
    val port: Int = when (val envPort = System.getenv("SENTINEL_SERVER_PORT")) {
        null -> 8080
        else -> envPort.toIntOrNull() ?: 8080
    }

    val jwt: JwtConfig = JwtConfig(
        issuer = System.getenv("SENTINEL_JWT_ISSUER") ?: "beryl-sentinel",
        audience = System.getenv("SENTINEL_JWT_AUDIENCE") ?: "beryl-super-app",
        realm = System.getenv("SENTINEL_JWT_REALM") ?: "sentinel"
    )
}
