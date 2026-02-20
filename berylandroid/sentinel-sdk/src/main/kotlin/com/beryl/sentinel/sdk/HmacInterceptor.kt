package com.beryl.sentinel.sdk

import okhttp3.Interceptor
import okhttp3.Response
import okio.Buffer
import java.util.UUID
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec

class HmacInterceptor(
    private val apiKey: String,
    private val apiSecret: String,
    private val deviceId: String
) : Interceptor {

    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()

        val timestamp = System.currentTimeMillis().toString()
        val nonce = UUID.randomUUID().toString()

        val payload = request.body?.let {
            val buffer = Buffer()
            it.writeTo(buffer)
            buffer.readUtf8()
        } ?: ""

        val signature = hmacSha256(apiSecret, "$apiKey$timestamp$nonce$deviceId$payload")

        val newRequest = request.newBuilder()
            .addHeader("X-API-KEY", apiKey)
            .addHeader("X-TIMESTAMP", timestamp)
            .addHeader("X-NONCE", nonce)
            .addHeader("X-DEVICE-ID", deviceId)
            .addHeader("X-SIGNATURE", signature)
            .build()

        return chain.proceed(newRequest)
    }

    private fun hmacSha256(secret: String, data: String): String {
        val algorithm = "HmacSHA256"
        val keySpec = SecretKeySpec(secret.toByteArray(), algorithm)
        val mac = Mac.getInstance(algorithm)
        mac.init(keySpec)
        return mac.doFinal(data.toByteArray()).joinToString(separator = "") { "%02x".format(it) }
    }
}
