package com.beryl.sentinel.sdk

import android.content.Context
import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.UUID

class SentinelClient(
    context: Context,
    private val baseUrl: String,
    private val apiKey: String,
    private val apiSecret: String
) {

    private val deviceId: String = UUID.randomUUID().toString()

    private val api: SentinelApi

    init {
        val client = OkHttpClient.Builder()
            .addInterceptor(HmacInterceptor(apiKey, apiSecret, deviceId))
            .build()

        val retrofit = Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()

        api = retrofit.create(SentinelApi::class.java)
    }

    suspend fun sendMessage(message: String, userContext: SentinelUserContext): SentinelResponse {
        val request = SentinelRequest(
            message = message,
            userContext = userContext
        )
        return api.sendMessage(request)
    }
}
