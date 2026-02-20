package com.beryl.berylandroid.observability

import android.util.Log
import com.beryl.berylandroid.BuildConfig

interface AppLogger {
    fun debug(tag: String, message: String)
    fun critical(
        tag: String,
        message: String,
        throwable: Throwable? = null,
        attributes: Map<String, String> = emptyMap()
    )
}

interface CriticalErrorReporter {
    fun capture(
        message: String,
        throwable: Throwable? = null,
        attributes: Map<String, String> = emptyMap()
    )
}

object NoOpCriticalErrorReporter : CriticalErrorReporter {
    override fun capture(
        message: String,
        throwable: Throwable?,
        attributes: Map<String, String>
    ) = Unit
}

class ProductionSafeLogger(
    private val reporter: CriticalErrorReporter = NoOpCriticalErrorReporter
) : AppLogger {
    override fun debug(tag: String, message: String) {
        if (BuildConfig.DEBUG) {
            Log.d(tag, message)
        }
    }

    override fun critical(
        tag: String,
        message: String,
        throwable: Throwable?,
        attributes: Map<String, String>
    ) {
        if (BuildConfig.DEBUG) {
            return
        }
        val formattedAttributes = if (attributes.isEmpty()) {
            ""
        } else {
            " | " + attributes.entries.joinToString(separator = ",") { "${it.key}=${it.value}" }
        }
        val finalMessage = message + formattedAttributes
        Log.e(tag, finalMessage, throwable)
        reporter.capture(
            message = finalMessage,
            throwable = throwable,
            attributes = attributes
        )
    }
}
