package com.beryl.sentinel.payment

import kotlinx.serialization.Serializable
import org.jetbrains.exposed.sql.Table
import org.jetbrains.exposed.sql.javatime.CurrentTimestamp
import org.jetbrains.exposed.sql.javatime.timestamp

object SavedBeneficiaries : Table("saved_beneficiaries") {
    val id = uuid("id")
    val ownerUid = text("owner_uid")
    val beneficiaryAccountId = text("beneficiary_account_id")
    val nickname = text("nickname").nullable()
    val lastUsedAt = timestamp("last_used_at").defaultExpression(CurrentTimestamp())

    init {
        uniqueIndex("unique_owner_beneficiary", ownerUid, beneficiaryAccountId)
    }

    override val primaryKey = PrimaryKey(id)
}

@Serializable
data class SaveBeneficiaryRequest(
    val accountId: String,
    val nickname: String? = null
)

@Serializable
data class SavedBeneficiaryResponse(
    val accountId: String,
    val nickname: String? = null,
    val lastUsedAt: String
)
