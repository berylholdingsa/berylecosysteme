package com.beryl.sentinel.server.routes

import io.ktor.server.application.call
import io.ktor.server.response.respond
import io.ktor.server.routing.Route
import io.ktor.server.routing.get
import kotlinx.serialization.Serializable

@Serializable
data class HealthResponse(val status: String)

internal fun Route.healthRoutes() {
    get("/health") {
        call.respond(HealthResponse("OK"))
    }
}
