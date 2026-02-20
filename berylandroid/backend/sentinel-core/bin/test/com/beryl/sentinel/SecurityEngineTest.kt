package com.beryl.sentinel

import com.beryl.sentinel.api.SentinelRequest
import com.beryl.sentinel.security.SecurityEngine
import kotlin.test.Test
import kotlin.test.assertTrue

class SecurityEngineTest {
    private val secret = "test-secret"
    private val engine = SecurityEngine(secret)

    @Test
    fun `valid request signature`() {
        val timestamp = System.currentTimeMillis() / 1000
        val payload = "Transfert de fonds"
        val nonce = "nonce-123"
        val deviceId = "device-abc"
        val signature = engine.sign(payload, timestamp, nonce, deviceId)
        val request = SentinelRequest(
            payload = payload,
            nonce = nonce,
            timestamp = timestamp,
            deviceId = deviceId,
            signature = signature
        )

        assertTrue(engine.validate(request))
    }
}
