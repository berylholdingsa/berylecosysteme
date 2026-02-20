package com.beryl.sentinel

import com.beryl.sentinel.api.SentinelRequest
import com.beryl.sentinel.engine.AOQResult
import com.beryl.sentinel.engine.IntentObject
import com.beryl.sentinel.ledger.LedgerEngine
import kotlin.test.Test
import kotlin.test.assertEquals

class LedgerEngineTest {
    private val ledger = LedgerEngine()

    @Test
    fun `record entry increases snapshot`() {
        val request = SentinelRequest(
            payload = "Test",
            deviceId = "device",
            nonce = "nonce",
            timestamp = System.currentTimeMillis() / 1000,
            signature = "sig"
        )
        val intent = IntentObject("chat", 0.5, emptyMap(), "bonjour")
        val result = AOQResult("committed", listOf("Chat"), "trace-1")
        ledger.record(request, intent, result)
        assertEquals(1, ledger.snapshot().size)
    }
}
