package com.beryl.sentinel.ledger

import com.beryl.sentinel.engine.AOQResult
import com.beryl.sentinel.engine.IntentObject
import com.beryl.sentinel.api.SentinelRequest

class LedgerEngine {
    private val journal = mutableListOf<LedgerEntry>()

    fun record(request: SentinelRequest, intent: IntentObject, result: AOQResult) {
        journal.add(
            LedgerEntry(
                traceId = result.traceId,
                intent = intent,
                status = result.status,
                services = result.actions,
                requester = request.deviceId,
                timestamp = request.timestamp
            )
        )
    }

    fun appendDebug(traceId: String, intent: IntentObject, status: String, services: List<String>) {
        journal.add(
            LedgerEntry(
                traceId = traceId,
                intent = intent,
                status = status,
                services = services,
                requester = "system",
                timestamp = System.currentTimeMillis()
            )
        )
    }

    fun snapshot(): List<LedgerEntry> = journal.toList()
}

data class LedgerEntry(
    val traceId: String,
    val intent: IntentObject,
    val status: String,
    val services: List<String>,
    val requester: String,
    val timestamp: Long
)
