package com.beryl.sentinel.server.services

import kotlinx.serialization.Serializable

@Serializable
internal data class SentinelAnalyzeRequest(
    val message: String,
    val userContext: SentinelUserContextPayload = SentinelUserContextPayload()
)

@Serializable
internal data class SentinelUserContextPayload(
    val firstName: String? = null,
    val role: String = "USER",
    val kycStatus: String = "PENDING",
    val riskScore: Float = 0f
)

internal data class AnalyzerInput(
    val message: String,
    val userContext: SentinelUserContextPayload
)

internal fun SentinelAnalyzeRequest.toAnalyzerInput(): AnalyzerInput =
    AnalyzerInput(message = message, userContext = userContext)
