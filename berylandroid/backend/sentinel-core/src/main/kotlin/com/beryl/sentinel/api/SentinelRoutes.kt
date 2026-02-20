package com.beryl.sentinel.api

import com.beryl.sentinel.engine.AOQOrchestrator
import com.beryl.sentinel.engine.IntentGenomeEngine
import com.beryl.sentinel.ledger.LedgerEngine
import com.beryl.sentinel.payment.BerylPayService
import com.beryl.sentinel.payment.configureBerylPayRoutes
import com.beryl.sentinel.security.JwtVerifier
import com.beryl.sentinel.security.NonceService
import com.beryl.sentinel.security.RateLimitService
import com.beryl.sentinel.security.SecurityEngine
import io.ktor.http.HttpStatusCode
import io.ktor.server.application.Application
import io.ktor.server.application.call
import io.ktor.server.request.receive
import io.ktor.server.response.respond
import io.ktor.server.routing.post
import io.ktor.server.routing.route
import io.ktor.server.routing.routing
import kotlinx.serialization.Serializable

fun Application.configureSentinelRoutes(
    intentEngine: IntentGenomeEngine,
    aoqOrchestrator: AOQOrchestrator,
    securityEngine: SecurityEngine,
    ledgerEngine: LedgerEngine,
    berylPayService: BerylPayService,
    jwtVerifier: JwtVerifier,
    rateLimitService: RateLimitService,
    nonceService: NonceService
) {
    routing {
        configureBerylPayRoutes(
            service = berylPayService,
            jwtVerifier = jwtVerifier,
            rateLimitService = rateLimitService,
            nonceService = nonceService
        )

        route("/sentinel") {
            post {
                val request = call.receive<SentinelRequest>()
                val isSecure = securityEngine.validate(request)
                if (!isSecure) {
                    return@post call.respond(
                        HttpStatusCode.Unauthorized,
                        SentinelResponse(
                            status = "failed",
                            intent = "security",
                            traceId = "unauthorized"
                        )
                    )
                }

                val intent = intentEngine.detectIntent(request.payload)
                val orchestration = aoqOrchestrator.orchestrate(intent, request.metadata)
                ledgerEngine.record(request, intent, orchestration)

                call.respond(
                    HttpStatusCode.OK,
                    SentinelResponse(
                        status = orchestration.status,
                        intent = intent.name,
                        actions = orchestration.actions,
                        traceId = orchestration.traceId
                    )
                )
            }
        }
    }
}

@Serializable
data class SentinelRequest(
    val payload: String,
    val deviceId: String,
    val nonce: String,
    val timestamp: Long,
    val signature: String,
    val metadata: Map<String, String> = emptyMap()
)

@Serializable
data class SentinelResponse(
    val status: String,
    val intent: String,
    val actions: List<String> = emptyList(),
    val traceId: String
)
