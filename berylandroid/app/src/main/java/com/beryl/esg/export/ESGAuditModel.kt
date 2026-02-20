package com.beryl.esg.export

data class ESGAuditRecord(
    val ville: String,
    val periode: String,
    val kmVerts: Double,
    val co2EviteKg: Double,
    val scoreEsg: Double,
    val classeImpact: String,
    val messageAoq: String
)
