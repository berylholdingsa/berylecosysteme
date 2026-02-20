package com.beryl.sentinel.sdk

import retrofit2.http.Body
import retrofit2.http.POST

interface SentinelApi {

    @POST("sentinel")
    suspend fun sendMessage(@Body request: SentinelRequest): SentinelResponse
}
