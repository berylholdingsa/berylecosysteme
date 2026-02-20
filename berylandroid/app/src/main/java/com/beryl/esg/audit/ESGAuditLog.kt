package com.beryl.esg.audit

data class ESGAuditLog(
    val timestamp: Long,
    val ville: String,
    val periode: String,
    val scoreEsg: Double,
    val hash: String
)
