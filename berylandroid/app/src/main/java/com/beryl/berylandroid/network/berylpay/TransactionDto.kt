package com.beryl.berylandroid.network.berylpay

data class TransactionDto(
    val id: String,
    val type: String,
    val amount: Double,
    val currency: String,
    val createdAt: String,
    val requestId: String
)
