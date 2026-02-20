class RateLimiter {
    suspend fun allow(key: String): Boolean = true
}
