package com.beryl.sentinel

import com.beryl.sentinel.api.configureSentinelRoutes
import com.beryl.sentinel.engine.AOQOrchestrator
import com.beryl.sentinel.engine.IntentGenomeEngine
import com.beryl.sentinel.ledger.LedgerEngine
import com.beryl.sentinel.payment.AccountSeed
import com.beryl.sentinel.payment.BerylPayService
import com.beryl.sentinel.payment.DatabaseFactory
import com.beryl.sentinel.security.FirebaseAuthVerifier
import com.beryl.sentinel.security.JwtVerifier
import com.beryl.sentinel.security.NonceService
import com.beryl.sentinel.security.RateLimitService
import com.beryl.sentinel.security.SecurityEngine
import com.beryl.sentinel.security.UnauthorizedException
import java.math.BigDecimal
import io.ktor.server.application.Application
import io.ktor.server.application.call
import io.ktor.server.application.install
import io.ktor.server.engine.embeddedServer
import io.ktor.server.netty.Netty
import io.ktor.serialization.kotlinx.json.json
import io.ktor.server.plugins.contentnegotiation.ContentNegotiation
import io.ktor.server.plugins.statuspages.StatusPages
import io.ktor.http.HttpStatusCode
import io.ktor.server.response.respond
import kotlinx.serialization.json.Json

fun main() {
    embeddedServer(Netty, port = 8080, host = "0.0.0.0") {
        module()
    }.start(wait = true)
}

fun Application.module(
    jwtVerifier: JwtVerifier = FirebaseAuthVerifier.fromEnvironment(),
    rateLimitService: RateLimitService = RateLimitService(),
    nonceService: NonceService = NonceService()
) {
    install(ContentNegotiation) {
        json(Json { prettyPrint = true; encodeDefaults = true })
    }
    install(StatusPages) {
        exception<UnauthorizedException> { call, _ ->
            call.respond(HttpStatusCode.Unauthorized, mapOf("error" to "Unauthorized"))
        }
    }

    DatabaseFactory.init()
    val berylPayService = BerylPayService().apply {
        seed(
            AccountSeed("beryl-core", BigDecimal("10000.00")),
            AccountSeed("client-wallet", BigDecimal("250.00"))
        )
    }

    val intentEngine = IntentGenomeEngine()
    val ledgerEngine = LedgerEngine()
    val securityEngine = SecurityEngine(secret = System.getenv("SENTINEL_SECRET") ?: "ultra-secret")
    val aoqOrchestrator = AOQOrchestrator(ledgerEngine, berylPayService)

    configureSentinelRoutes(
        intentEngine = intentEngine,
        aoqOrchestrator = aoqOrchestrator,
        securityEngine = securityEngine,
        ledgerEngine = ledgerEngine,
        berylPayService = berylPayService,
        jwtVerifier = jwtVerifier,
        rateLimitService = rateLimitService,
        nonceService = nonceService
    )
}
