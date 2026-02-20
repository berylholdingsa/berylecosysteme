package com.beryl.sentinel.payment

import org.jetbrains.exposed.sql.Table
import org.jetbrains.exposed.sql.javatime.CurrentTimestamp
import org.jetbrains.exposed.sql.javatime.timestamp

object BerylPayLedger : Table("beryl_pay_ledger") {
    val id = uuid("id")
    val accountId = text("account_id")
    val type = text("type")
    val amount = decimal("amount", 18, 2)
    val currency = varchar("currency", 8)
    val requestId = text("request_id")
    val correlationId = text("correlation_id")
    val nonce = text("nonce").nullable()
    val createdAt = timestamp("created_at").defaultExpression(CurrentTimestamp())
    val hash = text("hash")
    override val primaryKey = PrimaryKey(id)
}
