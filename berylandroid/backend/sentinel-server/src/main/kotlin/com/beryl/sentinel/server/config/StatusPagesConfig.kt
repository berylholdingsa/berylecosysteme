package com.beryl.sentinel.server.config

import com.beryl.sentinel.server.services.AnalyzerException
import io.ktor.http.HttpStatusCode
import io.ktor.server.application.call
import io.ktor.server.plugins.statuspages.StatusPagesConfig
import io.ktor.server.response.respond
import kotlinx.serialization.Serializable
import org.slf4j.LoggerFactory

@Serializable
internal data class ErrorResponse(
    val error: String,
    val details: String? = null
)

internal fun StatusPagesConfig.configureStatusPages() {
    val logger = LoggerFactory.getLogger("SentinelServerStatus")

    exception<IllegalArgumentException> { call, cause ->
        val errorMessage = cause.message ?: "invalid request"
        call.respond(
            HttpStatusCode.BadRequest,
            ErrorResponse(error = "invalid_request", details = errorMessage)
        )
    }

    exception<AnalyzerException> { call, cause ->
        call.respond(
            HttpStatusCode.UnprocessableEntity,
            ErrorResponse(error = "analysis_failed", details = cause.message ?: "analysis could not be completed")
        )
    }

    exception<Throwable> { call, cause ->
        logger.error("unexpected error", cause)
        call.respond(
            HttpStatusCode.InternalServerError,
            ErrorResponse(error = "internal_error", details = "an unexpected error occurred")
        )
    }
}
