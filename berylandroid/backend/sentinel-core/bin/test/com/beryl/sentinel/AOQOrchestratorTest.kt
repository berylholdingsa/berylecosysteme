package com.beryl.sentinel

import com.beryl.sentinel.engine.AOQOrchestrator
import com.beryl.sentinel.engine.IntentObject
import com.beryl.sentinel.ledger.LedgerEngine
import com.beryl.sentinel.payment.AccountSeed
import com.beryl.sentinel.payment.BerylPayService
import com.beryl.sentinel.payment.DatabaseFactory
import com.beryl.sentinel.payment.TopUpRequest
import kotlin.test.Test
import kotlin.test.assertEquals
import java.math.BigDecimal

class AOQOrchestratorTest {
    private val ledger = LedgerEngine()

    private val berylPayService: BerylPayService by lazy {
        DatabaseFactory.resetForTests()
        BerylPayService().apply {
            seed(
                AccountSeed("beryl-core", BigDecimal("500.00")),
                AccountSeed("client-wallet", BigDecimal("150.00"))
            )
        }
    }

    private val orchestrator by lazy {
        AOQOrchestrator(ledger, berylPayService)
    }

    @Test
    fun `orchestrate payment intent commits`() {
        // Ensure accounts have sufficient funds.
        berylPayService.topup(TopUpRequest("beryl-core", BigDecimal("250.00")))
        val intent = IntentObject(
            name = "payment",
            confidence = 0.86,
            entities = emptyMap(),
            rawMessage = "Transfère 120 euros vers client-wallet"
        )
        val metadata = mapOf(
            "amount" to "120.00",
            "fromAccount" to "beryl-core",
            "toAccount" to "client-wallet"
        )
        val result = orchestrator.orchestrate(intent, metadata)
        assertEquals("committed", result.status)
    }
}
