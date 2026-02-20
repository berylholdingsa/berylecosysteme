package com.beryl.sentinel.security

import java.util.concurrent.ConcurrentHashMap

interface NonceStore {
    fun putIfAbsent(nonce: String, expiresAtMillis: Long): Boolean
    fun evictExpired(nowMillis: Long)
}

class InMemoryNonceStore : NonceStore {
    private val nonces = ConcurrentHashMap<String, Long>()

    override fun putIfAbsent(nonce: String, expiresAtMillis: Long): Boolean {
        return nonces.putIfAbsent(nonce, expiresAtMillis) == null
    }

    override fun evictExpired(nowMillis: Long) {
        nonces.entries.removeIf { (_, expiresAt) -> expiresAt <= nowMillis }
    }
}

class NonceService(
    private val nonceStore: NonceStore = InMemoryNonceStore(),
    private val ttlMillis: Long = 2 * 60 * 1000L
) {
    fun register(nonce: String): Boolean {
        val cleaned = nonce.trim()
        if (cleaned.isEmpty()) {
            return false
        }
        val now = System.currentTimeMillis()
        nonceStore.evictExpired(now)
        return nonceStore.putIfAbsent(cleaned, now + ttlMillis)
    }
}
