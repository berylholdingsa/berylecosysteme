package com.beryl.sentinel.security

import com.beryl.sentinel.api.SentinelRequest
import java.nio.charset.StandardCharsets
import java.time.Instant
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec

class SecurityEngine(private val secret: String) {
    private val macAlgorithm = "HmacSHA256"

    fun sign(payload: String, timestamp: Long, nonce: String, deviceId: String): String {
        val base = "$payload::$timestamp::$nonce::$deviceId"
        val mac = Mac.getInstance(macAlgorithm)
        mac.init(SecretKeySpec(secret.toByteArray(StandardCharsets.UTF_8), macAlgorithm))
        return mac.doFinal(base.toByteArray(StandardCharsets.UTF_8)).joinToString(separator = "") { "%02x".format(it) }
    }

    fun validate(request: SentinelRequest): Boolean {
        val now = Instant.now().epochSecond
        val ageSeconds = now - request.timestamp
        if (ageSeconds > 120) return false
        val expected = sign(request.payload, request.timestamp, request.nonce, request.deviceId)
        return expected == request.signature && request.deviceId.isNotBlank()
    }
}
