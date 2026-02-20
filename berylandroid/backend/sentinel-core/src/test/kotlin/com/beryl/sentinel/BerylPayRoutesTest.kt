package com.beryl.sentinel

import com.beryl.sentinel.payment.BalanceResponse
import com.beryl.sentinel.payment.SaveBeneficiaryRequest
import com.beryl.sentinel.payment.SavedBeneficiaryResponse
import com.beryl.sentinel.payment.TransactionsResponse
import com.beryl.sentinel.security.AuthenticatedPrincipal
import com.beryl.sentinel.security.JwtVerifier
import com.beryl.sentinel.security.NonceService
import com.beryl.sentinel.security.RateLimitService
import com.beryl.sentinel.payment.TopUpRequest
import com.beryl.sentinel.payment.TransferRequest
import io.ktor.client.request.get
import io.ktor.client.request.header
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.client.statement.bodyAsText
import io.ktor.http.ContentType
import io.ktor.http.HttpStatusCode
import io.ktor.http.contentType
import io.ktor.server.testing.testApplication
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.util.UUID
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue
import java.math.BigDecimal

class BerylPayRoutesTest {
    private val json = Json { encodeDefaults = true }
    private val jwtVerifier = object : JwtVerifier {
        override fun verifyIdToken(token: String, checkRevoked: Boolean): AuthenticatedPrincipal {
            return when (token) {
                "valid-test-jwt" -> AuthenticatedPrincipal(uid = "test-user")
                "valid-other-jwt" -> AuthenticatedPrincipal(uid = "other-user")
                else -> throw IllegalArgumentException("Invalid token")
            }
        }
    }

    private fun io.ktor.client.request.HttpRequestBuilder.applyBaseSecurityHeaders(
        token: String = "valid-test-jwt"
    ) {
        header("Authorization", "Bearer $token")
        header("X-Client-Correlation-Id", "test-correlation-id")
        header("X-Device-Fingerprint", "test-fingerprint")
        header("X-Device-Rooted", "false")
        header("X-Request-Id", UUID.randomUUID().toString())
    }

    @Test
    fun `topup and balance endpoints succeed`() = testApplication {
        System.setProperty("SENTINEL_DATABASE_URL", "jdbc:h2:mem:payroutes-balance;DB_CLOSE_DELAY=-1")
        application {
            module(
                jwtVerifier = jwtVerifier,
                rateLimitService = RateLimitService(),
                nonceService = NonceService()
            )
        }

        val topUpRequest = TopUpRequest("test-user", BigDecimal("300.00"))
        val topUpResponse = client.post("/pay/topup") {
            applyBaseSecurityHeaders()
            header("X-Request-Nonce", "nonce-topup-1")
            contentType(ContentType.Application.Json)
            setBody(json.encodeToString(topUpRequest))
        }

        assertEquals(HttpStatusCode.OK, topUpResponse.status)
        val balanceResponse = client.get("/pay/balance?accountId=test-user") {
            applyBaseSecurityHeaders()
        }
        assertEquals(HttpStatusCode.OK, balanceResponse.status)
        val balance = Json.decodeFromString<BalanceResponse>(balanceResponse.bodyAsText())
        assertEquals("test-user", balance.accountId)
        assertEquals(BigDecimal("300.00"), balance.balance)

        val transactionsResponse = client.get("/pay/transactions") {
            applyBaseSecurityHeaders()
        }
        assertEquals(HttpStatusCode.OK, transactionsResponse.status)
        val transactions = Json.decodeFromString<TransactionsResponse>(transactionsResponse.bodyAsText())
        assertEquals("test-user", transactions.accountId)
        assertEquals(true, transactions.transactions.isNotEmpty())
        val firstTransaction = transactions.transactions.first()
        assertEquals("TOPUP", firstTransaction.type)
        assertEquals(true, firstTransaction.id.isNotBlank())
        assertEquals(true, firstTransaction.requestId.isNotBlank())
        assertEquals("EUR", firstTransaction.currency)
    }

    @Test
    fun `transfer endpoint debits payer and credits recipient`() = testApplication {
        System.setProperty("SENTINEL_DATABASE_URL", "jdbc:h2:mem:payroutes-transfer;DB_CLOSE_DELAY=-1")
        application {
            module(
                jwtVerifier = jwtVerifier,
                rateLimitService = RateLimitService(),
                nonceService = NonceService()
            )
        }

        val payerTopup = TopUpRequest("payer-account", BigDecimal("500.00"))
        client.post("/pay/topup") {
            applyBaseSecurityHeaders()
            header("X-Request-Nonce", "nonce-topup-2")
            contentType(ContentType.Application.Json)
            setBody(json.encodeToString(payerTopup))
        }

        val recipientTopup = TopUpRequest("recipient-account", BigDecimal("50.00"))
        client.post("/pay/topup") {
            applyBaseSecurityHeaders()
            header("X-Request-Nonce", "nonce-topup-3")
            contentType(ContentType.Application.Json)
            setBody(json.encodeToString(recipientTopup))
        }

        val transferRequest = TransferRequest("payer-account", "recipient-account", BigDecimal("120.00"))
        val transferResponse = client.post("/pay/transfer") {
            applyBaseSecurityHeaders()
            header("X-Request-Nonce", "nonce-transfer-1")
            contentType(ContentType.Application.Json)
            setBody(json.encodeToString(transferRequest))
        }

        assertEquals(HttpStatusCode.OK, transferResponse.status)
        val payerBalance = Json.decodeFromString<BalanceResponse>(
            client.get("/pay/balance?accountId=payer-account") {
                applyBaseSecurityHeaders()
            }.bodyAsText()
        )
        val recipientBalance = Json.decodeFromString<BalanceResponse>(
            client.get("/pay/balance?accountId=recipient-account") {
                applyBaseSecurityHeaders()
            }.bodyAsText()
        )

        assertEquals(BigDecimal("380.00"), payerBalance.balance)
        assertEquals(BigDecimal("170.00"), recipientBalance.balance)
    }

    @Test
    fun `beneficiaries endpoints use jwt uid and avoid duplicates`() = testApplication {
        System.setProperty("SENTINEL_DATABASE_URL", "jdbc:h2:mem:payroutes-beneficiaries;DB_CLOSE_DELAY=-1")
        application {
            module(
                jwtVerifier = jwtVerifier,
                rateLimitService = RateLimitService(),
                nonceService = NonceService()
            )
        }

        val firstSave = client.post("/pay/beneficiaries") {
            applyBaseSecurityHeaders()
            contentType(ContentType.Application.Json)
            setBody(json.encodeToString(SaveBeneficiaryRequest(accountId = "recipient-account", nickname = "Alice")))
        }
        assertEquals(HttpStatusCode.NoContent, firstSave.status)

        val duplicateSave = client.post("/pay/beneficiaries") {
            applyBaseSecurityHeaders()
            contentType(ContentType.Application.Json)
            setBody(
                json.encodeToString(
                    SaveBeneficiaryRequest(accountId = "recipient-account", nickname = "Alice Updated")
                )
            )
        }
        assertEquals(HttpStatusCode.NoContent, duplicateSave.status)

        val otherUserSave = client.post("/pay/beneficiaries") {
            applyBaseSecurityHeaders(token = "valid-other-jwt")
            contentType(ContentType.Application.Json)
            setBody(json.encodeToString(SaveBeneficiaryRequest(accountId = "recipient-account", nickname = "Bob")))
        }
        assertEquals(HttpStatusCode.NoContent, otherUserSave.status)

        val testUserList = client.get("/pay/beneficiaries") {
            applyBaseSecurityHeaders()
        }
        assertEquals(HttpStatusCode.OK, testUserList.status)
        val testUserBeneficiaries = json.decodeFromString<List<SavedBeneficiaryResponse>>(testUserList.bodyAsText())
        assertEquals(1, testUserBeneficiaries.size)
        assertEquals("recipient-account", testUserBeneficiaries.first().accountId)
        assertEquals("Alice Updated", testUserBeneficiaries.first().nickname)
        assertTrue(testUserBeneficiaries.first().lastUsedAt.isNotBlank())

        val otherUserList = client.get("/pay/beneficiaries") {
            applyBaseSecurityHeaders(token = "valid-other-jwt")
        }
        assertEquals(HttpStatusCode.OK, otherUserList.status)
        val otherUserBeneficiaries = json.decodeFromString<List<SavedBeneficiaryResponse>>(otherUserList.bodyAsText())
        assertEquals(1, otherUserBeneficiaries.size)
        assertEquals("recipient-account", otherUserBeneficiaries.first().accountId)
        assertEquals("Bob", otherUserBeneficiaries.first().nickname)
    }

    @Test
    fun `transfer auto saves beneficiary without duplication`() = testApplication {
        System.setProperty("SENTINEL_DATABASE_URL", "jdbc:h2:mem:payroutes-transfer-autosave;DB_CLOSE_DELAY=-1")
        application {
            module(
                jwtVerifier = jwtVerifier,
                rateLimitService = RateLimitService(),
                nonceService = NonceService()
            )
        }

        client.post("/pay/topup") {
            applyBaseSecurityHeaders()
            header("X-Request-Nonce", "nonce-topup-auto-1")
            contentType(ContentType.Application.Json)
            setBody(json.encodeToString(TopUpRequest("payer-account", BigDecimal("500.00"))))
        }

        client.post("/pay/topup") {
            applyBaseSecurityHeaders()
            header("X-Request-Nonce", "nonce-topup-auto-2")
            contentType(ContentType.Application.Json)
            setBody(json.encodeToString(TopUpRequest("recipient-account", BigDecimal("10.00"))))
        }

        val firstTransfer = client.post("/pay/transfer") {
            applyBaseSecurityHeaders()
            header("X-Request-Nonce", "nonce-transfer-auto-1")
            contentType(ContentType.Application.Json)
            setBody(json.encodeToString(TransferRequest("payer-account", "recipient-account", BigDecimal("50.00"))))
        }
        assertEquals(HttpStatusCode.OK, firstTransfer.status)

        val secondTransfer = client.post("/pay/transfer") {
            applyBaseSecurityHeaders()
            header("X-Request-Nonce", "nonce-transfer-auto-2")
            contentType(ContentType.Application.Json)
            setBody(json.encodeToString(TransferRequest("payer-account", "recipient-account", BigDecimal("20.00"))))
        }
        assertEquals(HttpStatusCode.OK, secondTransfer.status)

        val beneficiariesResponse = client.get("/pay/beneficiaries") {
            applyBaseSecurityHeaders()
        }
        assertEquals(HttpStatusCode.OK, beneficiariesResponse.status)
        val beneficiaries = json.decodeFromString<List<SavedBeneficiaryResponse>>(beneficiariesResponse.bodyAsText())
        assertEquals(1, beneficiaries.size)
        assertEquals("recipient-account", beneficiaries.first().accountId)
    }

    @Test
    fun `transactions pagination respects size`() = testApplication {
        System.setProperty("SENTINEL_DATABASE_URL", "jdbc:h2:mem:payroutes-transactions-pagination;DB_CLOSE_DELAY=-1")
        application {
            module(
                jwtVerifier = jwtVerifier,
                rateLimitService = RateLimitService(),
                nonceService = NonceService()
            )
        }

        repeat(5) { index ->
            val response = client.post("/pay/topup") {
                applyBaseSecurityHeaders()
                header("X-Request-Nonce", "nonce-pagination-topup-$index")
                contentType(ContentType.Application.Json)
                setBody(
                    json.encodeToString(
                        TopUpRequest(
                            accountId = "test-user",
                            amount = BigDecimal("${100 + index}.00")
                        )
                    )
                )
            }
            assertEquals(HttpStatusCode.OK, response.status)
        }

        val transactionsResponse = client.get("/pay/transactions?page=0&size=2") {
            applyBaseSecurityHeaders()
        }
        assertEquals(HttpStatusCode.OK, transactionsResponse.status)
        val transactions = json.decodeFromString<TransactionsResponse>(transactionsResponse.bodyAsText())
        assertEquals("test-user", transactions.accountId)
        assertEquals(2, transactions.transactions.size)
    }

    @Test
    fun `transactions filter CREDIT returns only credit entries`() = testApplication {
        System.setProperty("SENTINEL_DATABASE_URL", "jdbc:h2:mem:payroutes-transactions-credit;DB_CLOSE_DELAY=-1")
        application {
            module(
                jwtVerifier = jwtVerifier,
                rateLimitService = RateLimitService(),
                nonceService = NonceService()
            )
        }

        val topupOther = client.post("/pay/topup") {
            applyBaseSecurityHeaders(token = "valid-other-jwt")
            header("X-Request-Nonce", "nonce-credit-topup-other")
            contentType(ContentType.Application.Json)
            setBody(json.encodeToString(TopUpRequest("other-user", BigDecimal("200.00"))))
        }
        assertEquals(HttpStatusCode.OK, topupOther.status)

        val inboundTransfer = client.post("/pay/transfer") {
            applyBaseSecurityHeaders(token = "valid-other-jwt")
            header("X-Request-Nonce", "nonce-credit-transfer-inbound")
            contentType(ContentType.Application.Json)
            setBody(json.encodeToString(TransferRequest("other-user", "test-user", BigDecimal("40.00"))))
        }
        assertEquals(HttpStatusCode.OK, inboundTransfer.status)

        val transactionsResponse = client.get("/pay/transactions?type=CREDIT") {
            applyBaseSecurityHeaders(token = "valid-test-jwt")
        }
        assertEquals(HttpStatusCode.OK, transactionsResponse.status)
        val transactions = json.decodeFromString<TransactionsResponse>(transactionsResponse.bodyAsText())
        assertTrue(transactions.transactions.isNotEmpty())
        assertTrue(transactions.transactions.all { it.type.contains("CREDIT", ignoreCase = true) })
    }

    @Test
    fun `transactions filter DEBIT returns only debit entries`() = testApplication {
        System.setProperty("SENTINEL_DATABASE_URL", "jdbc:h2:mem:payroutes-transactions-debit;DB_CLOSE_DELAY=-1")
        application {
            module(
                jwtVerifier = jwtVerifier,
                rateLimitService = RateLimitService(),
                nonceService = NonceService()
            )
        }

        val topupTest = client.post("/pay/topup") {
            applyBaseSecurityHeaders(token = "valid-test-jwt")
            header("X-Request-Nonce", "nonce-debit-topup-test")
            contentType(ContentType.Application.Json)
            setBody(json.encodeToString(TopUpRequest("test-user", BigDecimal("300.00"))))
        }
        assertEquals(HttpStatusCode.OK, topupTest.status)

        val outboundTransfer = client.post("/pay/transfer") {
            applyBaseSecurityHeaders(token = "valid-test-jwt")
            header("X-Request-Nonce", "nonce-debit-transfer-outbound")
            contentType(ContentType.Application.Json)
            setBody(json.encodeToString(TransferRequest("test-user", "other-user", BigDecimal("35.00"))))
        }
        assertEquals(HttpStatusCode.OK, outboundTransfer.status)

        val transactionsResponse = client.get("/pay/transactions?type=DEBIT") {
            applyBaseSecurityHeaders(token = "valid-test-jwt")
        }
        assertEquals(HttpStatusCode.OK, transactionsResponse.status)
        val transactions = json.decodeFromString<TransactionsResponse>(transactionsResponse.bodyAsText())
        assertTrue(transactions.transactions.isNotEmpty())
        assertTrue(transactions.transactions.all { it.type.contains("DEBIT", ignoreCase = true) })
    }

    @Test
    fun `transactions endpoint isolates data by owner uid from jwt`() = testApplication {
        System.setProperty("SENTINEL_DATABASE_URL", "jdbc:h2:mem:payroutes-transactions-isolation;DB_CLOSE_DELAY=-1")
        application {
            module(
                jwtVerifier = jwtVerifier,
                rateLimitService = RateLimitService(),
                nonceService = NonceService()
            )
        }

        val topupTest = client.post("/pay/topup") {
            applyBaseSecurityHeaders(token = "valid-test-jwt")
            header("X-Request-Nonce", "nonce-isolation-topup-test")
            contentType(ContentType.Application.Json)
            setBody(json.encodeToString(TopUpRequest("test-user", BigDecimal("120.00"))))
        }
        assertEquals(HttpStatusCode.OK, topupTest.status)

        val topupOther = client.post("/pay/topup") {
            applyBaseSecurityHeaders(token = "valid-other-jwt")
            header("X-Request-Nonce", "nonce-isolation-topup-other")
            contentType(ContentType.Application.Json)
            setBody(json.encodeToString(TopUpRequest("other-user", BigDecimal("220.00"))))
        }
        assertEquals(HttpStatusCode.OK, topupOther.status)

        val testUserResponse = client.get("/pay/transactions") {
            applyBaseSecurityHeaders(token = "valid-test-jwt")
        }
        assertEquals(HttpStatusCode.OK, testUserResponse.status)
        val testUserTransactions = json.decodeFromString<TransactionsResponse>(testUserResponse.bodyAsText())
        assertEquals("test-user", testUserTransactions.accountId)
        assertEquals(1, testUserTransactions.transactions.size)
        assertEquals("TOPUP", testUserTransactions.transactions.first().type)

        val otherUserResponse = client.get("/pay/transactions") {
            applyBaseSecurityHeaders(token = "valid-other-jwt")
        }
        assertEquals(HttpStatusCode.OK, otherUserResponse.status)
        val otherUserTransactions = json.decodeFromString<TransactionsResponse>(otherUserResponse.bodyAsText())
        assertEquals("other-user", otherUserTransactions.accountId)
        assertEquals(1, otherUserTransactions.transactions.size)
        assertEquals("TOPUP", otherUserTransactions.transactions.first().type)
    }
}
