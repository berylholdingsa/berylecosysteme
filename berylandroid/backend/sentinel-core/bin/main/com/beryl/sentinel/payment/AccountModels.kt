package com.beryl.sentinel.payment

import org.jetbrains.exposed.sql.ResultRow
import org.jetbrains.exposed.sql.Table
import org.jetbrains.exposed.sql.Table.PrimaryKey
import org.jetbrains.exposed.sql.javatime.CurrentTimestamp
import org.jetbrains.exposed.sql.javatime.timestamp
import java.math.BigDecimal

object Accounts : Table("accounts") {
    val id = varchar("id", 64)
    val balance = decimal("balance", 18, 2)
    val currency = varchar("currency", 4).default("EUR")
    val createdAt = timestamp("created_at").defaultExpression(CurrentTimestamp())
    val updatedAt = timestamp("updated_at").defaultExpression(CurrentTimestamp())
    override val primaryKey = PrimaryKey(id)
}

data class Account(
    val id: String,
    val balance: BigDecimal,
    val currency: String
)

data class AccountSeed(
    val id: String,
    val balance: BigDecimal,
    val currency: String = "EUR"
)

fun ResultRow.toAccount(): Account {
    return Account(
        id = this[Accounts.id],
        balance = this[Accounts.balance],
        currency = this[Accounts.currency]
    )
}
