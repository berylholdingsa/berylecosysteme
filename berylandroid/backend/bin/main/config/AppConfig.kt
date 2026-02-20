object AppConfig {
    val port: Int = Env.getOrDefault("PORT", "8080").toInt()

    val firebaseProjectId: String = Env.getRequired("FIREBASE_PROJECT_ID")
    val firebaseCredentialsJson: String? = Env.get("FIREBASE_SERVICE_ACCOUNT_JSON")
    val firebaseCredentialsPath: String? = Env.get("FIREBASE_SERVICE_ACCOUNT_PATH")

    val rateLimitPerMinute: Int = Env.getOrDefault("RATE_LIMIT_PER_MINUTE", "120").toInt()
    val rateLimitBurst: Int = Env.getOrDefault("RATE_LIMIT_BURST", "30").toInt()

    val redisUrl: String? = Env.get("REDIS_URL")
    val redisHost: String? = Env.get("REDIS_HOST")
    val redisPort: Int = Env.getOrDefault("REDIS_PORT", "6379").toInt()
    val redisPassword: String? = Env.get("REDIS_PASSWORD")
    val redisTls: Boolean = Env.getOrDefault("REDIS_TLS", "false").toBoolean()

    val allowedOrigins: List<String> = Env.getOrDefault("CORS_ALLOWED_ORIGINS", "*")
        .split(',')
        .map { it.trim() }
        .filter { it.isNotEmpty() }
}
