package com.beryl.sentinel.sdk

import com.google.gson.annotations.SerializedName

data class SentinelUserContext(
    val firstName: String? = null,
    val role: String = "USER",
    val kycStatus: String = "PENDING",
    val riskScore: Float = 0f
)

data class SentinelRequest(
    val message: String,
    val userContext: SentinelUserContext
)

data class SentinelResponse(
    val intent: String,
    val actions: List<String>,
    @SerializedName("status")
    val result: String,
    val traceId: String
)
