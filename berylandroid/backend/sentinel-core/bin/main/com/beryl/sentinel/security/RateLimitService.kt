package com.beryl.sentinel.security

import java.util.concurrent.ConcurrentHashMap

class RateLimitService(
    private val accountLimitPerMinute: Int = 20,
    private val fingerprintLimitPerMinute: Int = 10,
    private val ipLimitPerMinute: Int = 50
) {
    private val counters = ConcurrentHashMap<String, Counter>()

    fun allow(accountId: String, fingerprint: String, ip: String): Boolean {
        val accountAllowed = incrementAndCheck(
            key = "acct:$accountId",
            limit = accountLimitPerMinute
        )
        val fingerprintAllowed = incrementAndCheck(
            key = "fingerprint:$fingerprint",
            limit = fingerprintLimitPerMinute
        )
        val ipAllowed = incrementAndCheck(
            key = "ip:$ip",
            limit = ipLimitPerMinute
        )
        return accountAllowed && fingerprintAllowed && ipAllowed
    }

    private fun incrementAndCheck(key: String, limit: Int): Boolean {
        val now = System.currentTimeMillis()
        val updated = counters.compute(key) { _, current ->
            if (current == null || now >= current.windowEndMillis) {
                Counter(count = 1, windowEndMillis = now + WINDOW_MILLIS)
            } else {
                current.copy(count = current.count + 1)
            }
        } ?: Counter(count = 1, windowEndMillis = now + WINDOW_MILLIS)
        return updated.count <= limit
    }

    private data class Counter(
        val count: Int,
        val windowEndMillis: Long
    )

    private companion object {
        private const val WINDOW_MILLIS = 60_000L
    }
}
