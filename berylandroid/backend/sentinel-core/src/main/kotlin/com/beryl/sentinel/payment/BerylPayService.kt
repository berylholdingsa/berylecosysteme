package com.beryl.sentinel.payment

import kotlinx.serialization.Serializable
import org.jetbrains.exposed.sql.SqlExpressionBuilder.eq
import org.jetbrains.exposed.sql.SqlExpressionBuilder.like
import org.jetbrains.exposed.sql.SortOrder
import org.jetbrains.exposed.sql.and
import org.jetbrains.exposed.sql.insert
import org.jetbrains.exposed.sql.select
import org.jetbrains.exposed.sql.transactions.transaction
import org.jetbrains.exposed.sql.update
import java.math.BigDecimal
import java.math.RoundingMode
import java.security.MessageDigest
import java.time.Instant
import java.util.UUID

data class RequestAuditContext(
    val requestId: String,
    val correlationId: String,
    val nonce: String? = null
) {
    companion object {
        fun generated(): RequestAuditContext {
            val generatedId = UUID.randomUUID().toString()
            return RequestAuditContext(
                requestId = generatedId,
                correlationId = generatedId
            )
        }
    }
}

class BerylPayService {
    fun seed(vararg seeds: AccountSeed) {
        transaction {
            seeds.forEach { seed ->
                val existing = Accounts.select { Accounts.id eq seed.id }.singleOrNull()
                if (existing == null) {
                    Accounts.insert {
                        it[id] = seed.id
                        it[balance] = seed.balance.setScale(2, RoundingMode.HALF_EVEN)
                        it[currency] = seed.currency
                    }
                }
            }
        }
    }

    fun transfer(
        request: TransferRequest,
        audit: RequestAuditContext = RequestAuditContext.generated()
    ): TransferResponse {
        return transaction {
            require(request.fromAccount != request.toAccount) { "Cannot transfer to the same account" }
            val amount = request.amount.setScale(2, RoundingMode.HALF_EVEN)
            require(amount > BigDecimal.ZERO) { "Transfer amount must be positive" }
            val now = Instant.now()

            val fromRow = Accounts
                .select { Accounts.id eq request.fromAccount }
                .forUpdate()
                .singleOrNull()
                ?: throw IllegalArgumentException("Source account not found: ${request.fromAccount}")
            val fromBalance = fromRow[Accounts.balance]
            require(fromBalance >= amount) { "Insufficient funds for ${request.fromAccount}" }

            val toRow = Accounts.select { Accounts.id eq request.toAccount }.singleOrNull()
            val toBalance = toRow?.get(Accounts.balance) ?: BigDecimal.ZERO

            Accounts.update({ Accounts.id eq request.fromAccount }) {
                it[balance] = fromBalance - amount
                it[Accounts.updatedAt] = now
            }

            if (toRow == null) {
                Accounts.insert {
                    it[id] = request.toAccount
                    it[balance] = amount
                    it[currency] = request.currency
                }
            } else {
                Accounts.update({ Accounts.id eq request.toAccount }) {
                    it[balance] = toBalance + amount
                    it[Accounts.updatedAt] = now
                }
            }

            appendImmutableLedgerEntry(
                accountId = request.fromAccount,
                type = "TRANSFER_DEBIT",
                amount = amount.negate(),
                currency = request.currency,
                requestId = audit.requestId,
                correlationId = audit.correlationId,
                nonce = audit.nonce,
                timestamp = now
            )
            appendImmutableLedgerEntry(
                accountId = request.toAccount,
                type = "TRANSFER_CREDIT",
                amount = amount,
                currency = request.currency,
                requestId = audit.requestId,
                correlationId = audit.correlationId,
                nonce = audit.nonce,
                timestamp = now
            )

            val updatedFrom = Accounts.select { Accounts.id eq request.fromAccount }.single()
            val updatedTo = Accounts.select { Accounts.id eq request.toAccount }.single()

            TransferResponse(
                traceId = UUID.randomUUID().toString(),
                fromAccount = request.fromAccount,
                toAccount = request.toAccount,
                amount = amount,
                status = "completed",
                fromBalance = updatedFrom[Accounts.balance],
                toBalance = updatedTo[Accounts.balance]
            )
        }
    }

    fun saveBeneficiary(ownerUid: String, accountId: String, nickname: String?) {
        transaction {
            require(ownerUid.isNotBlank()) { "ownerUid is required" }
            require(accountId.isNotBlank()) { "accountId is required" }

            val now = Instant.now()
            val normalizedNickname = nickname?.trim()?.takeIf { it.isNotEmpty() }
            val existing = SavedBeneficiaries.select {
                (SavedBeneficiaries.ownerUid eq ownerUid) and
                    (SavedBeneficiaries.beneficiaryAccountId eq accountId)
            }.singleOrNull()

            if (existing == null) {
                SavedBeneficiaries.insert {
                    it[id] = UUID.randomUUID()
                    it[SavedBeneficiaries.ownerUid] = ownerUid
                    it[SavedBeneficiaries.beneficiaryAccountId] = accountId
                    it[SavedBeneficiaries.nickname] = normalizedNickname
                    it[SavedBeneficiaries.lastUsedAt] = now
                }
            } else {
                SavedBeneficiaries.update({
                    (SavedBeneficiaries.ownerUid eq ownerUid) and
                        (SavedBeneficiaries.beneficiaryAccountId eq accountId)
                }) {
                    it[SavedBeneficiaries.lastUsedAt] = now
                    if (normalizedNickname != null) {
                        it[SavedBeneficiaries.nickname] = normalizedNickname
                    }
                }
            }
        }
    }

    fun listBeneficiaries(ownerUid: String): List<SavedBeneficiaryResponse> {
        return transaction {
            require(ownerUid.isNotBlank()) { "ownerUid is required" }

            SavedBeneficiaries
                .select { SavedBeneficiaries.ownerUid eq ownerUid }
                .orderBy(SavedBeneficiaries.lastUsedAt, SortOrder.DESC)
                .map { row ->
                    SavedBeneficiaryResponse(
                        accountId = row[SavedBeneficiaries.beneficiaryAccountId],
                        nickname = row[SavedBeneficiaries.nickname],
                        lastUsedAt = row[SavedBeneficiaries.lastUsedAt].toString()
                    )
                }
        }
    }

    fun topup(
        request: TopUpRequest,
        audit: RequestAuditContext = RequestAuditContext.generated()
    ): TopUpResponse {
        return transaction {
            require(request.amount > BigDecimal.ZERO) { "Top-up amount must be positive" }
            val amount = request.amount.setScale(2, RoundingMode.HALF_EVEN)
            val now = Instant.now()
            val existing = Accounts.select { Accounts.id eq request.accountId }.singleOrNull()

            if (existing == null) {
                Accounts.insert {
                    it[id] = request.accountId
                    it[balance] = amount
                    it[currency] = request.currency
                }
            } else {
                val currentBalance = existing[Accounts.balance]
                Accounts.update({ Accounts.id eq request.accountId }) {
                    it[balance] = currentBalance + amount
                    it[Accounts.updatedAt] = now
                }
            }

            appendImmutableLedgerEntry(
                accountId = request.accountId,
                type = "TOPUP",
                amount = amount,
                currency = request.currency,
                requestId = audit.requestId,
                correlationId = audit.correlationId,
                nonce = audit.nonce,
                timestamp = now
            )

            val refreshed = Accounts.select { Accounts.id eq request.accountId }.single()
            TopUpResponse(
                traceId = UUID.randomUUID().toString(),
                accountId = request.accountId,
                currency = refreshed[Accounts.currency],
                balance = refreshed[Accounts.balance]
            )
        }
    }

    fun balance(accountId: String): BalanceResponse {
        return transaction {
            val row = Accounts.select { Accounts.id eq accountId }.singleOrNull()
                ?: throw IllegalArgumentException("Account not found: $accountId")
            BalanceResponse(
                accountId = accountId,
                balance = row[Accounts.balance],
                currency = row[Accounts.currency]
            )
        }
    }

    fun transactions(
        ownerUid: String,
        page: Int = 0,
        size: Int = 20,
        type: TransactionTypeFilter? = null
    ): TransactionsResponse {
        return transaction {
            require(ownerUid.isNotBlank()) { "ownerUid is required" }
            require(page >= 0) { "page must be >= 0" }
            require(size in 1..50) { "size must be between 1 and 50" }

            val offset = page.toLong() * size.toLong()
            val ownerCriteria = BerylPayLedger.accountId eq ownerUid
            val whereClause = when (type) {
                TransactionTypeFilter.CREDIT -> ownerCriteria and (BerylPayLedger.type like "%CREDIT%")
                TransactionTypeFilter.DEBIT -> ownerCriteria and (BerylPayLedger.type like "%DEBIT%")
                null -> ownerCriteria
            }

            val items = BerylPayLedger
                .select { whereClause }
                .orderBy(BerylPayLedger.createdAt, SortOrder.DESC)
                .limit(size, offset)
                .map { row ->
                    TransactionItem(
                        id = row[BerylPayLedger.id].toString(),
                        type = row[BerylPayLedger.type],
                        amount = row[BerylPayLedger.amount],
                        currency = row[BerylPayLedger.currency],
                        createdAt = row[BerylPayLedger.createdAt].toString(),
                        requestId = row[BerylPayLedger.requestId]
                    )
                }
            TransactionsResponse(accountId = ownerUid, transactions = items)
        }
    }

    private fun appendImmutableLedgerEntry(
        accountId: String,
        type: String,
        amount: BigDecimal,
        currency: String,
        requestId: String,
        correlationId: String,
        nonce: String?,
        timestamp: Instant
    ) {
        val normalizedAmount = amount.setScale(2, RoundingMode.HALF_EVEN)
        val hash = computeLedgerHash(
            accountId = accountId,
            type = type,
            amount = normalizedAmount,
            currency = currency,
            requestId = requestId,
            timestamp = timestamp
        )
        BerylPayLedger.insert {
            it[id] = UUID.randomUUID()
            it[BerylPayLedger.accountId] = accountId
            it[BerylPayLedger.type] = type
            it[BerylPayLedger.amount] = normalizedAmount
            it[BerylPayLedger.currency] = currency
            it[BerylPayLedger.requestId] = requestId
            it[BerylPayLedger.correlationId] = correlationId
            it[BerylPayLedger.nonce] = nonce
            it[createdAt] = timestamp
            it[BerylPayLedger.hash] = hash
        }
    }

    private fun computeLedgerHash(
        accountId: String,
        type: String,
        amount: BigDecimal,
        currency: String,
        requestId: String,
        timestamp: Instant
    ): String {
        val raw = buildString {
            append(accountId)
            append(type)
            append(amount.toPlainString())
            append(currency)
            append(requestId)
            append(timestamp.toEpochMilli())
        }
        val digest = MessageDigest.getInstance("SHA-256").digest(raw.toByteArray())
        return digest.joinToString(separator = "") { byte -> "%02x".format(byte) }
    }
}

@Serializable
data class TransferRequest(
    val fromAccount: String,
    val toAccount: String,
    @Serializable(with = DecimalSerializer::class)
    val amount: BigDecimal,
    val currency: String = "EUR"
)

@Serializable
data class TransferResponse(
    val traceId: String,
    val fromAccount: String,
    val toAccount: String,
    @Serializable(with = DecimalSerializer::class)
    val amount: BigDecimal,
    val status: String,
    @Serializable(with = DecimalSerializer::class)
    val fromBalance: BigDecimal,
    @Serializable(with = DecimalSerializer::class)
    val toBalance: BigDecimal
)

@Serializable
data class TopUpRequest(
    val accountId: String,
    @Serializable(with = DecimalSerializer::class)
    val amount: BigDecimal,
    val currency: String = "EUR"
)

@Serializable
data class TopUpResponse(
    val traceId: String,
    val accountId: String,
    val currency: String,
    @Serializable(with = DecimalSerializer::class)
    val balance: BigDecimal
)

@Serializable
data class BalanceResponse(
    val accountId: String,
    val currency: String,
    @Serializable(with = DecimalSerializer::class)
    val balance: BigDecimal
)

@Serializable
data class TransactionItem(
    val id: String,
    val type: String,
    @Serializable(with = DecimalSerializer::class)
    val amount: BigDecimal,
    val currency: String,
    val createdAt: String,
    val requestId: String
)

enum class TransactionTypeFilter {
    CREDIT,
    DEBIT
}

@Serializable
data class TransactionsResponse(
    val accountId: String,
    val transactions: List<TransactionItem>
)
