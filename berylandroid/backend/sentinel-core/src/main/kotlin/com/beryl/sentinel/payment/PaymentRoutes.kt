package com.beryl.sentinel.payment

import io.ktor.http.HttpStatusCode
import io.ktor.server.application.ApplicationCall
import io.ktor.server.application.call
import io.ktor.server.response.respond
import io.ktor.server.routing.Route
import io.ktor.server.routing.get
import io.ktor.server.routing.post
import io.ktor.server.routing.route
import io.ktor.server.request.receive
import com.beryl.sentinel.security.JwtVerifier
import com.beryl.sentinel.security.NonceService
import com.beryl.sentinel.security.RateLimitService
import com.beryl.sentinel.security.UnauthorizedException
import com.beryl.sentinel.security.authenticateJwt
import com.beryl.sentinel.security.jwtPrincipal
import java.util.UUID

private const val HEADER_REQUEST_ID = "X-Request-Id"
private const val HEADER_CLIENT_CORRELATION_ID = "X-Client-Correlation-Id"
private const val HEADER_DEVICE_FINGERPRINT = "X-Device-Fingerprint"
private const val HEADER_DEVICE_ROOTED = "X-Device-Rooted"
private const val HEADER_REQUEST_NONCE = "X-Request-Nonce"
private const val DEFAULT_TRANSACTIONS_PAGE = 0
private const val DEFAULT_TRANSACTIONS_SIZE = 20
private const val MAX_TRANSACTIONS_SIZE = 50

fun Route.configureBerylPayRoutes(
    service: BerylPayService,
    jwtVerifier: JwtVerifier,
    rateLimitService: RateLimitService,
    nonceService: NonceService
) {
    route("/pay") {
        authenticateJwt(jwtVerifier) {
            post("/transfer") {
                val requestId = call.attachTracingHeaders()
                call.logClientSecurityContext(requestId)
                val nonce = call.request.headers[HEADER_REQUEST_NONCE]?.trim()
                if (nonce.isNullOrBlank()) {
                    return@post call.respond(
                        HttpStatusCode.BadRequest,
                        mapOf("error" to "X-Request-Nonce header is required")
                    )
                }
                if (!nonceService.register(nonce)) {
                    return@post call.respond(
                        HttpStatusCode.Conflict,
                        mapOf("error" to "Duplicate request nonce")
                    )
                }

                val principal = call.jwtPrincipal() ?: throw UnauthorizedException("Unauthorized")
                val request = call.receive<TransferRequest>()
                val fingerprint = call.request.headers[HEADER_DEVICE_FINGERPRINT] ?: "missing"
                val ip = call.request.local.remoteHost
                if (!rateLimitService.allow(request.fromAccount, fingerprint, ip)) {
                    return@post call.respond(
                        HttpStatusCode.TooManyRequests,
                        mapOf("error" to "Rate limit exceeded")
                    )
                }

                val result = service.transfer(
                    request = request,
                    audit = RequestAuditContext(
                        requestId = requestId,
                        correlationId = call.correlationId(requestId),
                        nonce = nonce
                    )
                )
                runCatching {
                    service.saveBeneficiary(
                        ownerUid = principal.uid,
                        accountId = request.toAccount,
                        nickname = null
                    )
                }.onFailure { error ->
                    call.application.environment.log.warn(
                        "berylpay-beneficiary-save-failed ownerUid=${principal.uid} accountId=${request.toAccount}",
                        error
                    )
                }
                call.respond(HttpStatusCode.OK, result)
            }

            get("/beneficiaries") {
                val requestId = call.attachTracingHeaders()
                call.logClientSecurityContext(requestId)
                val principal = call.jwtPrincipal() ?: throw UnauthorizedException("Unauthorized")
                val result = service.listBeneficiaries(ownerUid = principal.uid)
                call.respond(HttpStatusCode.OK, result)
            }

            post("/beneficiaries") {
                val requestId = call.attachTracingHeaders()
                call.logClientSecurityContext(requestId)
                val principal = call.jwtPrincipal() ?: throw UnauthorizedException("Unauthorized")
                val request = call.receive<SaveBeneficiaryRequest>()
                val normalizedAccountId = request.accountId.trim()
                if (normalizedAccountId.isBlank()) {
                    return@post call.respond(
                        HttpStatusCode.BadRequest,
                        mapOf("error" to "accountId is required")
                    )
                }
                service.saveBeneficiary(
                    ownerUid = principal.uid,
                    accountId = normalizedAccountId,
                    nickname = request.nickname
                )
                call.respond(HttpStatusCode.NoContent)
            }

            post("/topup") {
                val requestId = call.attachTracingHeaders()
                call.logClientSecurityContext(requestId)
                val nonce = call.request.headers[HEADER_REQUEST_NONCE]?.trim()
                if (nonce.isNullOrBlank()) {
                    return@post call.respond(
                        HttpStatusCode.BadRequest,
                        mapOf("error" to "X-Request-Nonce header is required")
                    )
                }
                if (!nonceService.register(nonce)) {
                    return@post call.respond(
                        HttpStatusCode.Conflict,
                        mapOf("error" to "Duplicate request nonce")
                    )
                }

                val request = call.receive<TopUpRequest>()
                val fingerprint = call.request.headers[HEADER_DEVICE_FINGERPRINT] ?: "missing"
                val ip = call.request.local.remoteHost
                if (!rateLimitService.allow(request.accountId, fingerprint, ip)) {
                    return@post call.respond(
                        HttpStatusCode.TooManyRequests,
                        mapOf("error" to "Rate limit exceeded")
                    )
                }

                val result = service.topup(
                    request = request,
                    audit = RequestAuditContext(
                        requestId = requestId,
                        correlationId = call.correlationId(requestId),
                        nonce = nonce
                    )
                )
                call.respond(HttpStatusCode.OK, result)
            }

            get("/balance") {
                val requestId = call.attachTracingHeaders()
                call.logClientSecurityContext(requestId)
                val accountId = call.request.queryParameters["accountId"]
                if (accountId.isNullOrBlank()) {
                    return@get call.respond(
                        HttpStatusCode.BadRequest,
                        mapOf("error" to "accountId query parameter is required")
                    )
                }
                val fingerprint = call.request.headers[HEADER_DEVICE_FINGERPRINT] ?: "missing"
                val ip = call.request.local.remoteHost
                if (!rateLimitService.allow(accountId, fingerprint, ip)) {
                    return@get call.respond(
                        HttpStatusCode.TooManyRequests,
                        mapOf("error" to "Rate limit exceeded")
                    )
                }
                val result = service.balance(accountId)
                call.respond(HttpStatusCode.OK, result)
            }

            get("/transactions") {
                val requestId = call.attachTracingHeaders()
                call.logClientSecurityContext(requestId)
                val principal = call.jwtPrincipal() ?: throw UnauthorizedException("Unauthorized")

                val rawPage = call.request.queryParameters["page"]
                val page = rawPage?.toIntOrNull() ?: if (rawPage == null) DEFAULT_TRANSACTIONS_PAGE else -1
                if (page < 0) {
                    return@get call.respond(
                        HttpStatusCode.BadRequest,
                        mapOf("error" to "page must be an integer >= 0")
                    )
                }

                val rawSize = call.request.queryParameters["size"]
                val size = rawSize?.toIntOrNull() ?: if (rawSize == null) DEFAULT_TRANSACTIONS_SIZE else -1
                if (size !in 1..MAX_TRANSACTIONS_SIZE) {
                    return@get call.respond(
                        HttpStatusCode.BadRequest,
                        mapOf("error" to "size must be an integer between 1 and $MAX_TRANSACTIONS_SIZE")
                    )
                }

                val rawType = call.request.queryParameters["type"]?.trim().orEmpty()
                val typeFilter = when {
                    rawType.isBlank() -> null
                    rawType.equals("CREDIT", ignoreCase = true) -> TransactionTypeFilter.CREDIT
                    rawType.equals("DEBIT", ignoreCase = true) -> TransactionTypeFilter.DEBIT
                    else -> {
                        return@get call.respond(
                            HttpStatusCode.BadRequest,
                            mapOf("error" to "type must be CREDIT or DEBIT")
                        )
                    }
                }
                val fingerprint = call.request.headers[HEADER_DEVICE_FINGERPRINT] ?: "missing"
                val ip = call.request.local.remoteHost
                if (!rateLimitService.allow(principal.uid, fingerprint, ip)) {
                    return@get call.respond(
                        HttpStatusCode.TooManyRequests,
                        mapOf("error" to "Rate limit exceeded")
                    )
                }
                val result = service.transactions(
                    ownerUid = principal.uid,
                    page = page,
                    size = size,
                    type = typeFilter
                )
                call.respond(HttpStatusCode.OK, result)
            }
        }
    }
}

private fun ApplicationCall.attachTracingHeaders(): String {
    val requestId = request.headers[HEADER_REQUEST_ID]
        ?.takeIf { it.isNotBlank() }
        ?: UUID.randomUUID().toString()
    response.headers.append(HEADER_REQUEST_ID, requestId)
    request.headers[HEADER_CLIENT_CORRELATION_ID]
        ?.takeIf { it.isNotBlank() }
        ?.let { correlationId ->
            response.headers.append(HEADER_CLIENT_CORRELATION_ID, correlationId)
        }
    return requestId
}

private fun ApplicationCall.correlationId(fallbackRequestId: String): String {
    return request.headers[HEADER_CLIENT_CORRELATION_ID]
        ?.takeIf { it.isNotBlank() }
        ?: fallbackRequestId
}

private fun ApplicationCall.logClientSecurityContext(requestId: String) {
    val correlationId = request.headers[HEADER_CLIENT_CORRELATION_ID] ?: "missing"
    val rooted = request.headers[HEADER_DEVICE_ROOTED] ?: "unknown"
    val deviceFingerprint = request.headers[HEADER_DEVICE_FINGERPRINT]
        ?.take(16)
        ?: "missing"
    application.environment.log.info(
        "berylpay-trace requestId=$requestId correlationId=$correlationId rooted=$rooted fingerprint=$deviceFingerprint"
    )
}
