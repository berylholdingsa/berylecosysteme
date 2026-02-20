package com.beryl.esg.data.repository

import com.beryl.berylandroid.BuildConfig
import com.google.gson.JsonObject
import com.google.gson.JsonParser
import com.google.gson.annotations.SerializedName
import java.io.IOException
import java.net.SocketTimeoutException
import java.util.concurrent.TimeUnit
import java.util.UUID
import okhttp3.OkHttpClient
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

sealed interface GreenOSRepositoryResult<out T> {
    data class Success<T>(val data: T) : GreenOSRepositoryResult<T>
    object Empty : GreenOSRepositoryResult<Nothing>
    data class Error(val code: String) : GreenOSRepositoryResult<Nothing>
}

data class GreenOSRealtimeCalculateRequest(
    @SerializedName("trip_id") val tripId: String,
    @SerializedName("user_id") val userId: String,
    @SerializedName("vehicle_id") val vehicleId: String,
    @SerializedName("country_code") val countryCode: String,
    @SerializedName("distance_km") val distanceKm: Double,
    @SerializedName("geo_hash") val geoHash: String,
    @SerializedName("model_version") val modelVersion: String? = null,
    @SerializedName("event_timestamp") val eventTimestamp: String? = null
)

data class GreenOSImpactResponse(
    @SerializedName("trip_id") val tripId: String?,
    @SerializedName("co2_avoided_kg") val co2AvoidedKg: Double?,
    @SerializedName("distance_km") val distanceKm: Double?,
    @SerializedName("country_code") val countryCode: String?,
    @SerializedName("event_hash") val eventHash: String?,
    @SerializedName("signature_algorithm") val signatureAlgorithm: String?,
    @SerializedName("model_version") val modelVersion: String?
)

data class GreenOSImpactConfidenceResponse(
    @SerializedName("confidence_score") val confidenceScore: Int?,
    @SerializedName("integrity_index") val integrityIndex: Int?,
    @SerializedName("aoq_status") val aoqStatus: String?,
    @SerializedName("anomaly_flags") val anomalyFlags: List<String>?
)

data class GreenOSImpactVerificationResponse(
    @SerializedName("verified") val verified: Boolean?,
    @SerializedName(value = "hash_valid", alternate = ["event_hash_valid"]) val eventHashValid: Boolean?,
    @SerializedName("signature_valid") val signatureValid: Boolean?,
    @SerializedName("asym_signature_valid") val asymSignatureValid: Boolean?
)

data class GreenOSMrvConfidencePayload(
    @SerializedName("average_confidence") val averageConfidence: Double?,
    @SerializedName("aoq_status") val aoqStatus: String?
)

data class GreenOSMrvMethodologyPayload(
    @SerializedName("model_version") val modelVersion: String?
)

data class GreenOSMrvExportPayload(
    @SerializedName("confidence_summary") val confidenceSummary: GreenOSMrvConfidencePayload?,
    @SerializedName("methodology") val methodology: GreenOSMrvMethodologyPayload?,
    @SerializedName("model_versions") val modelVersions: List<String>?
)

data class GreenOSMrvExportResponse(
    @SerializedName("export_id") val exportId: String?,
    @SerializedName("total_co2_avoided") val totalCo2Avoided: Double?,
    @SerializedName("total_distance") val totalDistance: Double?,
    @SerializedName("methodology_version") val methodologyVersion: String?,
    @SerializedName("payload") val payload: GreenOSMrvExportPayload?
)

data class GreenOSMrvConfidenceSummaryResponse(
    @SerializedName("average_confidence") val averageConfidence: Double?,
    @SerializedName("aoq_status") val aoqStatus: String?
)

data class GreenOSMethodologyResponse(
    @SerializedName("methodology_version") val methodologyVersion: String?,
    @SerializedName("emission_factor_source") val emissionFactorSource: String?,
    @SerializedName("geographic_scope") val geographicScope: String?,
    @SerializedName("status") val status: String?
)

private interface GreenOSApiService {
    @POST("api/v2/esg/realtime/calculate")
    suspend fun calculateRealtime(
        @Body request: GreenOSRealtimeCalculateRequest
    ): Response<GreenOSImpactResponse>

    @GET("api/v2/esg/impact/{tripId}")
    suspend fun getImpact(
        @Path("tripId") tripId: String
    ): Response<GreenOSImpactResponse>

    @GET("api/v2/esg/impact/{tripId}/confidence")
    suspend fun getImpactConfidence(
        @Path("tripId") tripId: String
    ): Response<GreenOSImpactConfidenceResponse>

    @GET("api/v2/esg/verify/{tripId}")
    suspend fun getImpactVerification(
        @Path("tripId") tripId: String
    ): Response<GreenOSImpactVerificationResponse>

    @GET("api/v2/esg/mrv/export")
    suspend fun getMrvExport(
        @Query("period") period: String
    ): Response<GreenOSMrvExportResponse>

    @GET("api/v2/esg/mrv/export/{exportId}/confidence-summary")
    suspend fun getMrvConfidenceSummary(
        @Path("exportId") exportId: String
    ): Response<GreenOSMrvConfidenceSummaryResponse>

    @GET("api/v2/esg/mrv/methodology/current")
    suspend fun getCurrentMethodology(): Response<GreenOSMethodologyResponse>

    @GET("api/v2/esg/health")
    suspend fun getHealth(): Response<JsonObject>
}

class GreenOSRepositoryV2 {

    private val api: GreenOSApiService? by lazy {
        val baseUrl = readConfiguredBaseUrl() ?: return@lazy null
        Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(buildHttpClient())
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(GreenOSApiService::class.java)
    }

    suspend fun calculateRealtime(
        request: GreenOSRealtimeCalculateRequest
    ): GreenOSRepositoryResult<GreenOSImpactResponse> {
        return execute { service -> service.calculateRealtime(request) }
    }

    suspend fun getImpact(
        tripId: String
    ): GreenOSRepositoryResult<GreenOSImpactResponse> {
        return execute { service -> service.getImpact(tripId) }
    }

    suspend fun getImpactConfidence(
        tripId: String
    ): GreenOSRepositoryResult<GreenOSImpactConfidenceResponse> {
        return execute { service -> service.getImpactConfidence(tripId) }
    }

    suspend fun getImpactVerification(
        tripId: String
    ): GreenOSRepositoryResult<GreenOSImpactVerificationResponse> {
        return execute { service -> service.getImpactVerification(tripId) }
    }

    suspend fun getMrvExport(
        period: String = "3M"
    ): GreenOSRepositoryResult<GreenOSMrvExportResponse> {
        return execute { service -> service.getMrvExport(period) }
    }

    suspend fun getMrvConfidenceSummary(
        exportId: String
    ): GreenOSRepositoryResult<GreenOSMrvConfidenceSummaryResponse> {
        return execute { service -> service.getMrvConfidenceSummary(exportId) }
    }

    suspend fun getCurrentMethodology(): GreenOSRepositoryResult<GreenOSMethodologyResponse> {
        return execute { service -> service.getCurrentMethodology() }
    }

    suspend fun checkGreenOSHealth(): GreenOSRepositoryResult<JsonObject> {
        return execute { service -> service.getHealth() }
    }

    private suspend fun <T : Any> execute(
        call: suspend (GreenOSApiService) -> Response<T>
    ): GreenOSRepositoryResult<T> {
        if (readConfiguredBaseUrl().isNullOrBlank()) {
            return GreenOSRepositoryResult.Error(ERROR_BASE_URL_NOT_CONFIGURED)
        }
        if (readConfiguredBearerToken().isNullOrBlank()) {
            return GreenOSRepositoryResult.Error(ERROR_UNAUTHORIZED)
        }
        val service = api ?: return GreenOSRepositoryResult.Error(ERROR_BASE_URL_NOT_CONFIGURED)
        return try {
            val response = call(service)
            if (response.isSuccessful) {
                val body = response.body()
                if (body == null) {
                    GreenOSRepositoryResult.Empty
                } else {
                    GreenOSRepositoryResult.Success(body)
                }
            } else {
                GreenOSRepositoryResult.Error(mapHttpError(response.errorBody()?.string(), response.code()))
            }
        } catch (exception: SocketTimeoutException) {
            GreenOSRepositoryResult.Error(ERROR_NETWORK_TIMEOUT)
        } catch (exception: IOException) {
            GreenOSRepositoryResult.Error(ERROR_NETWORK_IO)
        } catch (exception: Exception) {
            GreenOSRepositoryResult.Error(ERROR_UNEXPECTED)
        }
    }

    private fun readConfiguredBaseUrl(): String? {
        val raw = BuildConfig.ESG_BASE_URL.trim()
        if (raw.isBlank()) {
            return null
        }

        return if (raw.endsWith("/")) raw else "$raw/"
    }

    private fun buildHttpClient(): OkHttpClient {
        return OkHttpClient.Builder()
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(20, TimeUnit.SECONDS)
            .writeTimeout(20, TimeUnit.SECONDS)
            .addInterceptor { chain ->
                val requestBuilder = chain.request().newBuilder()
                    .header("X-Correlation-ID", UUID.randomUUID().toString())
                    .header("X-Nonce", UUID.randomUUID().toString())
                    .header("X-Timestamp", (System.currentTimeMillis() / 1000L).toString())
                    .header("X-Scope", "esg")

                val configuredToken = readConfiguredBearerToken()
                if (!configuredToken.isNullOrBlank()) {
                    val token = if (configuredToken.startsWith("Bearer ")) {
                        configuredToken
                    } else {
                        "Bearer $configuredToken"
                    }
                    requestBuilder.header("Authorization", token)
                }

                chain.proceed(requestBuilder.build())
            }
            .build()
    }

    private fun readConfiguredBearerToken(): String? {
        val raw = BuildConfig.GREENOS_BEARER_TOKEN.trim()
        return raw.takeIf { it.isNotEmpty() }
    }

    private fun extractErrorCode(
        raw: String?,
        httpCode: Int
    ): String {
        if (raw.isNullOrBlank()) {
            return "HTTP_$httpCode"
        }

        return runCatching {
            val root = JsonParser.parseString(raw)
            if (!root.isJsonObject) {
                return@runCatching "HTTP_$httpCode"
            }

            val rootObject = root.asJsonObject
            readCode(rootObject)
                ?: readCode(rootObject.getAsJsonObjectOrNull("detail"))
                ?: "HTTP_$httpCode"
        }.getOrElse {
            "HTTP_$httpCode"
        }
    }

    private fun mapHttpError(raw: String?, httpCode: Int): String {
        return when (httpCode) {
            401 -> ERROR_UNAUTHORIZED
            403 -> ERROR_FORBIDDEN
            else -> extractErrorCode(raw, httpCode)
        }
    }

    private fun readCode(source: JsonObject?): String? {
        if (source == null || !source.has("code")) {
            return null
        }
        val codeElement = source.get("code")
        return if (codeElement != null && codeElement.isJsonPrimitive) {
            codeElement.asString
        } else {
            null
        }
    }

    private fun JsonObject.getAsJsonObjectOrNull(memberName: String): JsonObject? {
        if (!has(memberName)) {
            return null
        }
        val element = get(memberName)
        return if (element != null && element.isJsonObject) {
            element.asJsonObject
        } else {
            null
        }
    }

    companion object {
        const val ERROR_BASE_URL_NOT_CONFIGURED: String = "ESG_BASE_URL_NOT_CONFIGURED"
        const val ERROR_UNAUTHORIZED: String = "UNAUTHORIZED"
        const val ERROR_FORBIDDEN: String = "FORBIDDEN"
        const val ERROR_NETWORK_TIMEOUT: String = "NETWORK_TIMEOUT"
        const val ERROR_NETWORK_IO: String = "NETWORK_IO_ERROR"
        const val ERROR_UNEXPECTED: String = "UNEXPECTED_ERROR"
    }
}
