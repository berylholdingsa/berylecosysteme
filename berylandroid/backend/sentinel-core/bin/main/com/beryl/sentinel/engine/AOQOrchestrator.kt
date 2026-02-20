package com.beryl.sentinel.engine

import com.beryl.sentinel.ledger.LedgerEngine
import com.beryl.sentinel.payment.BerylPayService
import com.beryl.sentinel.payment.PaymentIntentParser
import com.beryl.sentinel.payment.TransferRequest
import java.util.UUID

class AOQOrchestrator(
    private val ledgerEngine: LedgerEngine,
    private val berylPayService: BerylPayService,
    private val paymentIntentParser: PaymentIntentParser = PaymentIntentParser
) {

    fun orchestrate(intent: IntentObject, metadata: Map<String, String>): AOQResult {
        val traceId = UUID.randomUUID().toString()
        val actions = mutableListOf<String>()
        var status = "committed"

        try {
            when (intent.name) {
                "payment" -> actions += executePayment(intent, metadata)
                "mobility" -> actions += "MobiliteWorkflow"
                "esg" -> actions += "ESGReporting"
                "profile" -> actions += "ProfileSync"
                else -> actions += "ChatFallback"
            }
        } catch (error: Exception) {
            status = "rolled_back"
            actions += "rollback:${error.message}"
        }

        ledgerEngine.appendDebug(traceId, intent, status, actions)
        return AOQResult(status = status, actions = actions, traceId = traceId)
    }

    private fun executePayment(intent: IntentObject, metadata: Map<String, String>): String {
        val paymentIntent = paymentIntentParser.parse(intent, metadata)
        val response = berylPayService.transfer(
            TransferRequest(
                fromAccount = paymentIntent.fromAccount,
                toAccount = paymentIntent.toAccount,
                amount = paymentIntent.amount,
                currency = paymentIntent.currency
            )
        )
        return "BerylPay:${response.fromAccount}->${response.toAccount}:${response.amount.toPlainString()}"
    }
}

data class AOQResult(
    val status: String,
    val actions: List<String>,
    val traceId: String
)
