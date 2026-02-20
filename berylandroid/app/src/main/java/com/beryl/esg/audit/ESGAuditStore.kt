package com.beryl.esg.audit

import android.content.Context
import java.io.File
import java.security.MessageDigest

class ESGAuditStore(private val context: Context) {

    private val file = File(context.filesDir, "esg_audit_log.txt")

    fun saveLog(ville: String, periode: String, score: Double, content: String) {
        val hash = sha256(content)
        val line = "${System.currentTimeMillis()},$ville,$periode,$score,$hash\n"
        file.appendText(line)
    }

    private fun sha256(input: String): String {
        val bytes = MessageDigest.getInstance("SHA-256").digest(input.toByteArray())
        return bytes.joinToString("") { "%02x".format(it) }
    }
}
