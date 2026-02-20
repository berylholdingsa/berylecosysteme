package com.beryl.sentinel.engine

class IntentGenomeEngine {
    fun detectIntent(message: String): IntentObject {
        val normalized = message.lowercase().trim().normalize()
        val intent = when {
            listOf("transf", "envoy", "payer").any { normalized.contains(it) } -> "payment"
            listOf("commande", "taxi", "ve", "voiture", "ve").any { normalized.contains(it) } -> "mobility"
            listOf("impact", "carbone", "esg").any { normalized.contains(it) } -> "esg"
            listOf("profil", "securite", "kyc").any { normalized.contains(it) } -> "profile"
            else -> "chat"
        }
        val confidence = normalized.length / 512.0.coerceAtMost(1.0)
        val entities = mutableMapOf<String, String>()
        if (normalized.contains("berylpay")) entities["service"] = "berylpay"
        return IntentObject(
            name = intent,
            confidence = confidence.coerceIn(0.1, 0.99),
            entities = entities,
            rawMessage = message
        )
    }
}

@JvmInline
value class IntentId(val value: String)

data class IntentObject(
    val name: String,
    val confidence: Double,
    val entities: Map<String, String>,
    val rawMessage: String
)

private fun String.normalize(): String {
    val replacements = mapOf(
        'é' to 'e',
        'è' to 'e',
        'ê' to 'e',
        'ë' to 'e',
        'à' to 'a',
        'ù' to 'u'
    )
    return this.map { replacements[it] ?: it }.joinToString(separator = "")
}
