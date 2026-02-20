package com.beryl.sentinel.server

import com.beryl.sentinel.server.config.SentinelServerConfig
import com.beryl.sentinel.server.config.configureStatusPages
import com.beryl.sentinel.server.routes.healthRoutes
import com.beryl.sentinel.server.routes.sentinelRoutes
import com.beryl.sentinel.server.services.AnalyzerService
import io.ktor.server.application.Application
import io.ktor.server.application.install
import io.ktor.server.engine.embeddedServer
import io.ktor.server.netty.Netty
import io.ktor.serialization.kotlinx.json.json
import io.ktor.server.plugins.callloging.CallLogging
import io.ktor.server.plugins.contentnegotiation.ContentNegotiation
import io.ktor.server.plugins.statuspages.StatusPages
import io.ktor.server.routing.routing
import kotlinx.serialization.json.Json

fun main() {
    embeddedServer(
        Netty,
        port = SentinelServerConfig.port,
        host = "0.0.0.0"
    ) {
        module()
    }.start(wait = true)
}

fun Application.module() {
    install(CallLogging)
    install(ContentNegotiation) {
        json(Json {
            prettyPrint = true
            encodeDefaults = true
        })
    }
    install(StatusPages) {
        configureStatusPages()
    }

    val analyzerService = AnalyzerService()

    routing {
        healthRoutes()
        sentinelRoutes(analyzerService)
    }
}
