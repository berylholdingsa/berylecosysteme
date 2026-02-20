package com.beryl.esg.ui.state

data class ESGHomeContent(
    val totalCo2Avoided: Double,
    val totalDistance: Double,
    val aoqStatus: String,
    val averageConfidence: Double,
    val modelVersion: String
)

data class ESGImpactDetailContent(
    val co2AvoidedKg: Double,
    val distanceKm: Double,
    val countryCode: String,
    val eventHash: String,
    val signatureAlgorithm: String,
    val modelVersion: String
)

data class ESGConfidenceContent(
    val confidenceScore: Int,
    val integrityIndex: Int,
    val aoqStatus: String,
    val anomalyFlags: List<String>
)

data class ESGVerificationContent(
    val verified: Boolean,
    val hashValid: Boolean,
    val signatureValid: Boolean,
    val asymSignatureValid: Boolean
)

data class ESGMrvReportContent(
    val totalCo2Avoided: Double,
    val methodologyVersion: String,
    val averageConfidence: Double,
    val aoqStatus: String
)

data class ESGMethodologyContent(
    val methodologyVersion: String,
    val emissionFactorSource: String,
    val geographicScope: String,
    val status: String
)
