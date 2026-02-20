package com.beryl.sentinel.server.routes

import com.beryl.sentinel.server.services.AnalyzerService
import com.beryl.sentinel.server.services.SentinelAnalyzeRequest
import com.beryl.sentinel.server.services.toAnalyzerInput
import com.beryl.sentinel.server.services.toResponse
import io.ktor.server.application.call
import io.ktor.server.request.receive
import io.ktor.server.response.respond
import io.ktor.server.routing.Route
import io.ktor.server.routing.post
import io.ktor.server.routing.route

internal fun Route.sentinelRoutes(analyzerService: AnalyzerService) {
    route("/sentinel") {
        post("/analyze") {
            val request = call.receive<SentinelAnalyzeRequest>()
            val analysis = analyzerService.analyze(request.toAnalyzerInput())
            call.respond(analysis.toResponse())
        }
    }
}
