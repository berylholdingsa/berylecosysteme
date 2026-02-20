package com.beryl.sentinel.payment

import com.beryl.sentinel.engine.IntentObject
import java.math.BigDecimal
import java.math.RoundingMode

data class PaymentIntent(
    val fromAccount: String,
    val toAccount: String,
    val amount: BigDecimal,
    val currency: String
)

object PaymentIntentParser {
    private val amountRegex = """(\d+(?:[.,]\d+)?)""".toRegex()
    private const val DefaultSource = "beryl-core"
    private const val DefaultDestination = "client-wallet"
    private const val DefaultCurrency = "EUR"

    fun parse(intent: IntentObject, metadata: Map<String, String>): PaymentIntent {
        val amount = metadata["amount"]?.toBigDecimalOrNull()
            ?: extractAmount(intent.rawMessage)
            ?: throw IllegalArgumentException("Unable to determine transfer amount")
        val fromAccount = metadata["fromAccount"] ?: metadata["sourceAccount"] ?: DefaultSource
        val toAccount = metadata["toAccount"] ?: metadata["destinationAccount"] ?: DefaultDestination
        val currency = metadata["currency"] ?: DefaultCurrency
        return PaymentIntent(
            fromAccount = fromAccount,
            toAccount = toAccount,
            amount = amount.setScale(2, RoundingMode.HALF_EVEN),
            currency = currency
        )
    }

    private fun extractAmount(message: String): BigDecimal? {
        val sanitized = message.replace(",", ".")
        return amountRegex.find(sanitized)?.value?.toBigDecimalOrNull()
    }
}
