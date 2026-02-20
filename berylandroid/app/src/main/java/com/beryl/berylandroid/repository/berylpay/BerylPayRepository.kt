package com.beryl.berylandroid.repository.berylpay

import android.util.Log
import com.beryl.berylandroid.BuildConfig
import com.beryl.berylandroid.network.berylpay.AuthInterceptor
import com.beryl.berylandroid.network.berylpay.BeneficiaryDto
import com.beryl.berylandroid.network.berylpay.BerylPaySessionExpiredException
import com.beryl.berylandroid.network.berylpay.LedgerApi
import com.beryl.berylandroid.network.berylpay.SaveBeneficiaryRequest
import com.beryl.berylandroid.network.berylpay.TransactionDto
import com.beryl.berylandroid.observability.AppLogger
import com.beryl.berylandroid.observability.ProductionSafeLogger
import com.beryl.berylandroid.security.DeviceSecurityManager
import com.beryl.berylandroid.session.SessionManager
import com.beryl.berylandroid.session.TokenRefreshManager
import okhttp3.CertificatePinner
import okhttp3.Headers
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.Response
import okhttp3.HttpUrl.Companion.toHttpUrlOrNull
import retrofit2.HttpException
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.io.IOException
import java.util.concurrent.TimeUnit

class BerylPayRepository(
    private val sessionManager: SessionManager = SessionManager,
    private val logger: AppLogger = ProductionSafeLogger(),
    baseUrl: String = resolveBaseUrl()
) {

    private val api: LedgerApi

    init {
        val selectedBaseUrl = normalizeBaseUrl(baseUrl)
        if (!BuildConfig.DEBUG && !selectedBaseUrl.startsWith("https://")) {
            throw IllegalStateException("BASE_URL_PROD must use HTTPS.")
        }

        val clientBuilder = OkHttpClient.Builder()
            .connectTimeout(NETWORK_TIMEOUT_SECONDS, TimeUnit.SECONDS)
            .readTimeout(NETWORK_TIMEOUT_SECONDS, TimeUnit.SECONDS)
            .retryOnConnectionFailure(true)
            .addInterceptor(
                AuthInterceptor(
                    tokenProvider = { TokenRefreshManager.getValidToken(sessionManager) },
                    forceRefreshTokenProvider = {
                        TokenRefreshManager.refreshToken(
                            forceRefresh = true,
                            sessionManager = sessionManager
                        )
                    },
                    correlationIdProvider = sessionManager::getOrCreateCorrelationId,
                    deviceFingerprintProvider = DeviceSecurityManager::getFingerprint,
                    rootedProvider = DeviceSecurityManager::isRooted,
                    onUnauthorized = sessionManager::clearSession
                )
            )
        if (!BuildConfig.DEBUG) {
            clientBuilder.certificatePinner(buildCertificatePinner(selectedBaseUrl))
        }
        if (BuildConfig.DEBUG) {
            clientBuilder.addInterceptor(HttpTraceInterceptor())
        }
        val client = clientBuilder.build()

        val retrofit = Retrofit.Builder()
            .baseUrl(selectedBaseUrl)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()

        api = retrofit.create(LedgerApi::class.java)
    }

    suspend fun fetchBalance(accountId: String): NetworkResult<BalanceSnapshot> {
        return try {
            val response = api.getBalance(accountId)
            val requestId = extractRequestId(response.headers())
            if (!response.isSuccessful) {
                logger.critical(
                    tag = TAG,
                    message = "BerylPay API error",
                    attributes = mapOf(
                        "code" to response.code().toString(),
                        "requestId" to (requestId ?: "missing")
                    )
                )
                NetworkResult.ApiError(response.code(), requestId)
            } else {
                val body = response.body()
                if (body == null) {
                    logger.critical(
                        tag = TAG,
                        message = "BerylPay API returned empty body",
                        attributes = mapOf("requestId" to (requestId ?: "missing"))
                    )
                    NetworkResult.UnknownError
                } else {
                    logger.debug(
                        tag = TAG,
                        message = "BerylPay balance response received (requestId=${requestId ?: "n/a"})"
                    )
                    NetworkResult.Success(
                        BalanceSnapshot(
                            amount = body.balance,
                            currency = body.currency
                        )
                    )
                }
            }
        } catch (_: BerylPaySessionExpiredException) {
            logger.critical(
                tag = TAG,
                message = "BerylPay session expired (401)",
                attributes = mapOf("code" to SESSION_EXPIRED_CODE.toString())
            )
            NetworkResult.ApiError(SESSION_EXPIRED_CODE)
        } catch (error: HttpException) {
            val requestId = extractRequestId(error.response()?.headers())
            logger.critical(
                tag = TAG,
                message = "BerylPay HTTP exception",
                throwable = error,
                attributes = mapOf(
                    "code" to error.code().toString(),
                    "requestId" to (requestId ?: "missing")
                )
            )
            NetworkResult.ApiError(error.code(), requestId)
        } catch (_: IOException) {
            logger.critical(
                tag = TAG,
                message = "BerylPay network I/O failure"
            )
            NetworkResult.NetworkError
        } catch (error: Exception) {
            logger.critical(
                tag = TAG,
                message = "BerylPay unknown failure",
                throwable = error
            )
            NetworkResult.UnknownError
        }
    }

    suspend fun fetchBeneficiaries(): NetworkResult<List<BeneficiaryDto>> {
        return try {
            val beneficiaries = api.getBeneficiaries()
            logger.debug(
                tag = TAG,
                message = "BerylPay beneficiaries fetched (count=${beneficiaries.size})"
            )
            NetworkResult.Success(beneficiaries)
        } catch (_: BerylPaySessionExpiredException) {
            logger.critical(
                tag = TAG,
                message = "BerylPay session expired while fetching beneficiaries",
                attributes = mapOf("code" to SESSION_EXPIRED_CODE.toString())
            )
            NetworkResult.ApiError(SESSION_EXPIRED_CODE)
        } catch (error: HttpException) {
            val requestId = extractRequestId(error.response()?.headers())
            logger.critical(
                tag = TAG,
                message = "BerylPay beneficiaries HTTP exception",
                throwable = error,
                attributes = mapOf(
                    "code" to error.code().toString(),
                    "requestId" to (requestId ?: "missing")
                )
            )
            NetworkResult.ApiError(error.code(), requestId)
        } catch (_: IOException) {
            logger.critical(
                tag = TAG,
                message = "BerylPay beneficiaries network I/O failure"
            )
            NetworkResult.NetworkError
        } catch (error: Exception) {
            logger.critical(
                tag = TAG,
                message = "BerylPay beneficiaries unknown failure",
                throwable = error
            )
            NetworkResult.UnknownError
        }
    }

    suspend fun saveBeneficiary(accountId: String): Boolean {
        val normalized = accountId.trim()
        if (normalized.isBlank()) {
            return false
        }
        try {
            api.saveBeneficiary(
                SaveBeneficiaryRequest(accountId = normalized)
            )
            logger.debug(
                tag = TAG,
                message = "BerylPay beneficiary saved (accountId=$normalized)"
            )
            return true
        } catch (_: BerylPaySessionExpiredException) {
            logger.critical(
                tag = TAG,
                message = "BerylPay session expired while saving beneficiary",
                attributes = mapOf("code" to SESSION_EXPIRED_CODE.toString())
            )
        } catch (error: HttpException) {
            val requestId = extractRequestId(error.response()?.headers())
            logger.critical(
                tag = TAG,
                message = "BerylPay save beneficiary HTTP exception",
                throwable = error,
                attributes = mapOf(
                    "code" to error.code().toString(),
                    "requestId" to (requestId ?: "missing")
                )
            )
        } catch (_: IOException) {
            logger.critical(
                tag = TAG,
                message = "BerylPay save beneficiary network I/O failure"
            )
        } catch (error: Exception) {
            logger.critical(
                tag = TAG,
                message = "BerylPay save beneficiary unknown failure",
                throwable = error
            )
        }
        return false
    }

    suspend fun fetchTransactions(
        page: Int = 0,
        size: Int = 20,
        type: String? = null
    ): NetworkResult<List<TransactionDto>> {
        return try {
            val response = api.getTransactions(page = page, size = size, type = type)
            val transactions = response.transactions
            logger.debug(
                tag = TAG,
                message = "BerylPay transactions fetched (count=${transactions.size})"
            )
            NetworkResult.Success(transactions)
        } catch (_: BerylPaySessionExpiredException) {
            logger.critical(
                tag = TAG,
                message = "BerylPay session expired while fetching transactions",
                attributes = mapOf("code" to SESSION_EXPIRED_CODE.toString())
            )
            NetworkResult.ApiError(SESSION_EXPIRED_CODE)
        } catch (error: HttpException) {
            val requestId = extractRequestId(error.response()?.headers())
            logger.critical(
                tag = TAG,
                message = "BerylPay transactions HTTP exception",
                throwable = error,
                attributes = mapOf(
                    "code" to error.code().toString(),
                    "requestId" to (requestId ?: "missing")
                )
            )
            NetworkResult.ApiError(error.code(), requestId)
        } catch (_: IOException) {
            logger.critical(
                tag = TAG,
                message = "BerylPay transactions network I/O failure"
            )
            NetworkResult.NetworkError
        } catch (error: Exception) {
            logger.critical(
                tag = TAG,
                message = "BerylPay transactions unknown failure",
                throwable = error
            )
            NetworkResult.UnknownError
        }
    }

    companion object {
        private const val TAG = "BerylPayRepository"
        private const val NETWORK_TIMEOUT_SECONDS = 10L
        private const val SESSION_EXPIRED_CODE = 401
        private val REQUEST_ID_HEADERS = listOf(
            "X-Request-Id",
            "X-Request-ID",
            "x-request-id"
        )

        private fun resolveBaseUrl(): String {
            return if (BuildConfig.DEBUG) {
                BuildConfig.BASE_URL_DEBUG
            } else {
                BuildConfig.BASE_URL_PROD
            }
        }

        private fun normalizeBaseUrl(baseUrl: String): String {
            val trimmed = baseUrl.trim()
            return if (trimmed.endsWith("/")) trimmed else "$trimmed/"
        }

        private fun buildCertificatePinner(baseUrl: String): CertificatePinner {
            val host = baseUrl.toHttpUrlOrNull()?.host
                ?: throw IllegalStateException("Invalid BASE_URL_PROD for certificate pinning.")
            val pins = listOf(
                BuildConfig.BERYLPAY_CERT_PIN_PRIMARY,
                BuildConfig.BERYLPAY_CERT_PIN_BACKUP
            )
                .map { it.trim() }
                .filter { it.startsWith("sha256/") }
            if (pins.isEmpty()) {
                throw IllegalStateException("Missing certificate pin(s) for release build.")
            }
            val builder = CertificatePinner.Builder()
            pins.forEach { pin ->
                builder.add(host, pin)
            }
            return builder.build()
        }

        private fun extractRequestId(headers: Headers?): String? {
            if (headers == null) {
                return null
            }
            for (headerName in REQUEST_ID_HEADERS) {
                val value = headers[headerName]?.trim()
                if (!value.isNullOrEmpty()) {
                    return value
                }
            }
            return null
        }
    }
}

private class HttpTraceInterceptor : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()
        val path = request.url.encodedPath
        Log.d("BerylPayHttp", "-> ${request.method} $path")
        return try {
            val response = chain.proceed(request)
            Log.d("BerylPayHttp", "<- ${response.code} ${request.method} $path")
            response
        } catch (error: Exception) {
            Log.e("BerylPayHttp", "xx ${request.method} $path: ${error.message}")
            throw error
        }
    }
}
