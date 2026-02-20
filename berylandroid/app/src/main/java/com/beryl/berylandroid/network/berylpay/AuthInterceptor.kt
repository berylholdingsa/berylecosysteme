package com.beryl.berylandroid.network.berylpay

import okhttp3.Interceptor
import okhttp3.Response

class AuthInterceptor(
    private val tokenProvider: () -> String?,
    private val forceRefreshTokenProvider: () -> String?,
    private val correlationIdProvider: () -> String?,
    private val deviceFingerprintProvider: () -> String?,
    private val rootedProvider: () -> Boolean,
    private val onUnauthorized: () -> Unit
) : Interceptor {

    override fun intercept(chain: Interceptor.Chain): Response {
        val token = tokenProvider()?.trim().orEmpty()
        val correlationId = correlationIdProvider()?.trim().orEmpty()
        val fingerprint = deviceFingerprintProvider()?.trim().orEmpty()
        val rooted = rootedProvider().toString()
        val baseRequest = chain.request()
        val request = baseRequest.newBuilder().apply {
            if (token.isNotEmpty()) {
                addHeader("Authorization", "Bearer $token")
            }
            if (correlationId.isNotEmpty()) {
                addHeader("X-Client-Correlation-Id", correlationId)
            }
            if (fingerprint.isNotEmpty()) {
                addHeader("X-Device-Fingerprint", fingerprint)
            }
            addHeader("X-Device-Rooted", rooted)
        }.build()
        val response = chain.proceed(request)
        if (response.code == 401) {
            response.close()
            val refreshedToken = forceRefreshTokenProvider()?.trim().orEmpty()
            if (refreshedToken.isNotEmpty() && refreshedToken != token) {
                val retryRequest = baseRequest.newBuilder().apply {
                    header("Authorization", "Bearer $refreshedToken")
                    if (correlationId.isNotEmpty()) {
                        header("X-Client-Correlation-Id", correlationId)
                    }
                    if (fingerprint.isNotEmpty()) {
                        header("X-Device-Fingerprint", fingerprint)
                    }
                    header("X-Device-Rooted", rooted)
                }.build()
                val retryResponse = chain.proceed(retryRequest)
                if (retryResponse.code != 401) {
                    return retryResponse
                }
                retryResponse.close()
            }
            onUnauthorized()
            throw BerylPaySessionExpiredException()
        }
        return response
    }
}
