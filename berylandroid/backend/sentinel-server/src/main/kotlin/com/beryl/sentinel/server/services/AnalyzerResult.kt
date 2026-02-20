package com.beryl.sentinel.server.services

import kotlinx.serialization.Serializable

internal data class AnalyzerResult(
    val score: Double,
    val decision: String,
    val intent: String,
    val actions: List<String>,
    val metadata: Map<String, String>,
    val traceId: String
)

@Serializable
internal data class SentinelAnalysisResponse(
    val score: Double,
    val decision: String,
    val intent: String,
    val actions: List<String>,
    val metadata: Map<String, String>,
    val traceId: String
)

internal fun AnalyzerResult.toResponse(): SentinelAnalysisResponse = SentinelAnalysisResponse(
    score = score,
    decision = decision,
    intent = intent,
    actions = actions,
    metadata = metadata,
    traceId = traceId
)

internal class AnalyzerException(message: String) : RuntimeException(message)

internal enum class AnalysisDecision {
    APPROVE,
    REVIEW,
    BLOCK
}

internal data class AnalyzerServiceConfig(
    val lowRiskThreshold: Double = 35.0,
    val highRiskThreshold: Double = 70.0,
    val maxMessageLength: Int = 256,
    val userRiskWeight: Double = 0.55,
    val keywordWeight: Double = 0.25,
    val lengthWeight: Double = 0.2
)
