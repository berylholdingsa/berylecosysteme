package com.beryl.sentinel.payment

import com.zaxxer.hikari.HikariConfig
import com.zaxxer.hikari.HikariDataSource
import org.jetbrains.exposed.sql.Database
import org.jetbrains.exposed.sql.SchemaUtils
import org.jetbrains.exposed.sql.deleteAll
import org.jetbrains.exposed.sql.transactions.transaction

object DatabaseFactory {
    private const val DefaultUrl = "jdbc:h2:mem:beryl;DB_CLOSE_DELAY=-1"
    private const val DefaultDriver = "org.h2.Driver"
    private const val DefaultUser = "sa"
    private const val DefaultPassword = ""

    fun init(
        url: String? = null,
        driver: String? = null,
        user: String? = null,
        password: String? = null
    ) {
        val configuredUrl = url
            ?: System.getProperty("SENTINEL_DATABASE_URL")
            ?: System.getenv("DATABASE_URL")
            ?: DefaultUrl
        val resolvedUrl = normalizeJdbcUrl(configuredUrl)
        val resolvedDriver = driver ?: determineDriverForUrl(resolvedUrl)
        val resolvedUser = user ?: System.getenv("DB_USER") ?: System.getProperty("SENTINEL_DB_USER") ?: DefaultUser
        val resolvedPassword =
            password ?: System.getenv("DB_PASSWORD") ?: System.getProperty("SENTINEL_DB_PASSWORD") ?: DefaultPassword

        val config = HikariConfig().apply {
            jdbcUrl = resolvedUrl
            driverClassName = resolvedDriver
            username = resolvedUser
            this.password = resolvedPassword
            maximumPoolSize = 5
            isAutoCommit = false
        }

        Database.connect(HikariDataSource(config))

        transaction {
            SchemaUtils.createMissingTablesAndColumns(Accounts, BerylPayLedger, SavedBeneficiaries)
        }
    }

    private fun determineDriverForUrl(url: String): String {
        return when {
            url.startsWith("jdbc:postgresql", ignoreCase = true) -> "org.postgresql.Driver"
            url.startsWith("postgresql://", ignoreCase = true) -> "org.postgresql.Driver"
            url.startsWith("postgres://", ignoreCase = true) -> "org.postgresql.Driver"
            url.startsWith("jdbc:h2", ignoreCase = true) -> "org.h2.Driver"
            else -> DefaultDriver
        }
    }

    private fun normalizeJdbcUrl(url: String): String {
        return when {
            url.startsWith("jdbc:", ignoreCase = true) -> url
            url.startsWith("postgresql://", ignoreCase = true) -> "jdbc:$url"
            url.startsWith("postgres://", ignoreCase = true) -> {
                val suffix = url.removePrefix("postgres://")
                "jdbc:postgresql://$suffix"
            }
            else -> url
        }
    }

    fun resetForTests() {
        init(url = DefaultUrl, driver = DefaultDriver, user = DefaultUser, password = DefaultPassword)
        transaction {
            SavedBeneficiaries.deleteAll()
            BerylPayLedger.deleteAll()
            Accounts.deleteAll()
        }
    }
}
