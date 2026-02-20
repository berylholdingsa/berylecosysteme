package com.beryl.sentinel.server.services

import com.beryl.sentinel.engine.IntentGenomeEngine
import org.slf4j.LoggerFactory
import java.time.Instant
import java.util.UUID

internal class AnalyzerService(
    private val config: AnalyzerServiceConfig = AnalyzerServiceConfig(),
    private val intentEngine: IntentGenomeEngine = IntentGenomeEngine()
) {
    private val logger = LoggerFactory.getLogger(AnalyzerService::class.java)
    private val keywordBoosts = mapOf(
        "transfer" to 0.45,
        "urgent" to 0.35,
        "loan" to 0.35,
        "verify" to 0.25,
        "password" to 0.5,
        "account" to 0.15
    )

    internal fun analyze(input: AnalyzerInput): AnalyzerResult {
        val message = input.message.trim().takeIf { it.isNotBlank() }
            ?: throw AnalyzerException("message must not be blank")

        val intent = intentEngine.detectIntent(message)
        val severity = computeSeverity(message, input.userContext)
        val decision = selectDecision(severity)
        val actions = actionsForDecision(decision)
        val traceId = UUID.randomUUID().toString()
        val metadata = mapOf(
            "intentName" to intent.name,
            "intentConfidence" to intent.confidence.toString(),
            "entities" to intent.entities.toString(),
            "userRole" to input.userContext.role,
            "kycStatus" to input.userContext.kycStatus,
            "analysisTime" to Instant.now().toString()
        )

        logger.debug("analysis trace=$traceId severity=$severity decision=$decision")
        return AnalyzerResult(
            score = severity,
            decision = decision.name,
            intent = intent.name,
            actions = actions,
            metadata = metadata,
            traceId = traceId
        )
    }

    private fun computeSeverity(message: String, context: SentinelUserContextPayload): Double {
        val normalizedLength = (message.length.coerceAtMost(config.maxMessageLength).toDouble() / config.maxMessageLength) * 100.0
        val baseRisk = (context.riskScore * 100.0).coerceIn(0.0, 100.0)
        val keywordScore = keywordBoosts.entries
            .filter { message.contains(it.key, ignoreCase = true) }
            .sumOf { it.value }
            .coerceAtMost(1.0)

        return (baseRisk * config.userRiskWeight) +
            (keywordScore * 100.0 * config.keywordWeight) +
            (normalizedLength * config.lengthWeight)
    }

    private fun selectDecision(severity: Double): AnalysisDecision = when {
        severity < config.lowRiskThreshold -> AnalysisDecision.APPROVE
        severity < config.highRiskThreshold -> AnalysisDecision.REVIEW
        else -> AnalysisDecision.BLOCK
    }

    private fun actionsForDecision(decision: AnalysisDecision): List<String> = when (decision) {
        AnalysisDecision.APPROVE -> listOf("notify_user", "log_event")
        AnalysisDecision.REVIEW -> listOf("flag_team", "request_additional_context")
        AnalysisDecision.BLOCK -> listOf("lock_operation", "alert_security")
    }
}
