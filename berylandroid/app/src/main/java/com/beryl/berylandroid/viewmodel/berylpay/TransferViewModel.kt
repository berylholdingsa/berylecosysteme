package com.beryl.berylandroid.viewmodel.berylpay

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.beryl.berylandroid.BuildConfig
import com.beryl.berylandroid.network.berylpay.AuthInterceptor
import com.beryl.berylandroid.network.berylpay.BeneficiaryDto
import com.beryl.berylandroid.network.berylpay.BerylPaySessionExpiredException
import com.beryl.berylandroid.repository.berylpay.BerylPayRepository
import com.beryl.berylandroid.repository.berylpay.NetworkResult
import com.beryl.berylandroid.security.DeviceSecurityManager
import com.beryl.berylandroid.session.SessionManager
import com.beryl.berylandroid.session.TokenRefreshManager
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import okhttp3.CertificatePinner
import okhttp3.HttpUrl.Companion.toHttpUrlOrNull
import okhttp3.OkHttpClient
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.Header
import retrofit2.http.POST
import java.io.IOException
import java.math.BigDecimal
import java.math.RoundingMode
import java.time.Instant
import java.util.UUID
import java.util.concurrent.TimeUnit

data class SavedBeneficiary(
    val id: String,
    val name: String,
    val accountId: String
)

data class TransferUiState(
    val balance: Double = 0.0,
    val currency: String = "EUR",
    val searchQuery: String = "",
    val selectedBeneficiary: SavedBeneficiary? = null,
    val amountInput: String = "",
    val canContinue: Boolean = false,
    val showSuggestions: Boolean = true,
    val showConfirmationSheet: Boolean = false,
    val isSubmitting: Boolean = false,
    val successTraceId: String? = null,
    val errorMessage: String? = null
)

class TransferViewModel(
    private val repository: BerylPayRepository = BerylPayRepository(),
    private val sessionManager: SessionManager = SessionManager
) : ViewModel() {

    private val transferApi: TransferApi by lazy { buildTransferApi() }

    private val _uiState = MutableStateFlow(TransferUiState())
    val uiState: StateFlow<TransferUiState> = _uiState.asStateFlow()

    private val _beneficiaries = MutableStateFlow<List<BeneficiaryDto>>(emptyList())
    val beneficiaries: StateFlow<List<BeneficiaryDto>> = _beneficiaries.asStateFlow()

    init {
        fetchBeneficiaries()
    }

    fun initializeBalance(balance: Double, currency: String) {
        val state = _uiState.value
        if (state.balance == balance && state.currency == currency) {
            return
        }
        _uiState.value = state.copy(balance = balance, currency = currency)
    }

    fun onSearchQueryChanged(query: String) {
        val accountId = query.trim()
        val selected = accountId.takeIf { it.isNotEmpty() }?.let {
            SavedBeneficiary(
                id = "manual-$it",
                name = it,
                accountId = it
            )
        }
        val currentState = _uiState.value
        _uiState.value = currentState.copy(
            searchQuery = query,
            selectedBeneficiary = selected,
            canContinue = isContinueEnabled(selected, currentState.amountInput),
            showSuggestions = true,
            errorMessage = null
        )
    }

    fun selectBeneficiarySuggestion(beneficiary: BeneficiaryDto) {
        val mapped = beneficiary.toSavedBeneficiary()
        val currentState = _uiState.value
        _uiState.value = currentState.copy(
            selectedBeneficiary = mapped,
            searchQuery = mapped.accountId,
            canContinue = isContinueEnabled(mapped, currentState.amountInput),
            showSuggestions = false,
            errorMessage = null
        )
    }

    fun onAmountChanged(rawAmount: String) {
        val sanitized = sanitizeAmountInput(rawAmount)
        val currentState = _uiState.value
        _uiState.value = currentState.copy(
            amountInput = sanitized,
            canContinue = isContinueEnabled(currentState.selectedBeneficiary, sanitized),
            errorMessage = null
        )
    }

    fun requestConfirmation() {
        val currentState = _uiState.value
        if (!currentState.canContinue) {
            _uiState.value = currentState.copy(
                errorMessage = "Veuillez saisir un compte bénéficiaire et un montant valide."
            )
            return
        }
        _uiState.value = currentState.copy(showConfirmationSheet = true, errorMessage = null)
    }

    fun canProceedToConfirmation(): Boolean {
        val currentState = _uiState.value
        if (!currentState.canContinue) {
            _uiState.value = currentState.copy(
                errorMessage = "Veuillez saisir un compte bénéficiaire et un montant valide."
            )
            return false
        }
        _uiState.value = currentState.copy(errorMessage = null)
        return true
    }

    fun dismissConfirmation() {
        val currentState = _uiState.value
        _uiState.value = currentState.copy(showConfirmationSheet = false)
    }

    fun clearSuccess() {
        val currentState = _uiState.value
        _uiState.value = currentState.copy(successTraceId = null)
    }

    fun confirmTransfer() {
        val currentState = _uiState.value
        val beneficiary = currentState.selectedBeneficiary
            ?: currentState.searchQuery.trim().takeIf { it.isNotEmpty() }?.let {
                SavedBeneficiary(
                    id = "manual-$it",
                    name = it,
                    accountId = it
                )
            }
        val amount = parseAmount(currentState.amountInput)

        if (beneficiary == null || amount == null) {
            _uiState.value = currentState.copy(
                showConfirmationSheet = false,
                errorMessage = "Informations de transfert incomplètes."
            )
            return
        }

        val fromAccount = sessionManager.getAccountId()?.takeIf { it.isNotBlank() }
        if (fromAccount == null) {
            _uiState.value = currentState.copy(
                showConfirmationSheet = false,
                errorMessage = "Session invalide. Veuillez vous reconnecter."
            )
            return
        }

        _uiState.value = currentState.copy(
            showConfirmationSheet = false,
            isSubmitting = true,
            errorMessage = null
        )

        viewModelScope.launch {
            try {
                val nonce = UUID.randomUUID().toString()
                val response = transferApi.transfer(
                    nonce = nonce,
                    request = TransferRequestDto(
                        fromAccount = fromAccount,
                        toAccount = beneficiary.accountId,
                        amount = amount,
                        currency = currentState.currency
                    )
                )
                val body = response.body()
                if (response.isSuccessful && body != null) {
                    _uiState.value = _uiState.value.copy(
                        isSubmitting = false,
                        successTraceId = body.traceId,
                        balance = body.fromBalance,
                        searchQuery = "",
                        amountInput = "",
                        selectedBeneficiary = null,
                        canContinue = false,
                        showSuggestions = false,
                        errorMessage = null
                    )

                    // Save does not block the transfer success flow.
                    viewModelScope.launch {
                        saveBeneficiaryAfterTransfer(body.toAccount.ifBlank { beneficiary.accountId })
                    }
                } else {
                    _uiState.value = _uiState.value.copy(
                        isSubmitting = false,
                        errorMessage = "Transfert impossible (code ${response.code()})."
                    )
                }
            } catch (_: BerylPaySessionExpiredException) {
                _uiState.value = _uiState.value.copy(
                    isSubmitting = false,
                    errorMessage = "Session expirée. Veuillez vous reconnecter."
                )
            } catch (_: IOException) {
                _uiState.value = _uiState.value.copy(
                    isSubmitting = false,
                    errorMessage = "Erreur réseau. Réessayez."
                )
            } catch (_: Exception) {
                _uiState.value = _uiState.value.copy(
                    isSubmitting = false,
                    errorMessage = "Une erreur inattendue est survenue."
                )
            }
        }
    }

    private fun fetchBeneficiaries() {
        viewModelScope.launch {
            when (val result = repository.fetchBeneficiaries()) {
                is NetworkResult.Success -> {
                    _beneficiaries.value = result.data.sortedByDescending {
                        parseLastUsedAt(it.lastUsedAt)
                    }
                }
                else -> Unit
            }
        }
    }

    private suspend fun saveBeneficiaryAfterTransfer(accountId: String) {
        val normalized = accountId.trim()
        if (normalized.isBlank()) {
            return
        }
        val saved = repository.saveBeneficiary(normalized)
        if (!saved) {
            return
        }

        val updated = _beneficiaries.value
            .filterNot { it.beneficiaryAccountId.equals(normalized, ignoreCase = true) }
            .plus(
                BeneficiaryDto(
                    id = normalized,
                    beneficiaryAccountId = normalized,
                    nickname = null,
                    lastUsedAt = Instant.now().toString()
                )
            )
            .sortedByDescending { parseLastUsedAt(it.lastUsedAt) }
        _beneficiaries.value = updated
    }

    private fun parseLastUsedAt(value: String): Instant {
        return runCatching {
            Instant.parse(value)
        }.getOrElse {
            Instant.EPOCH
        }
    }

    private fun BeneficiaryDto.toSavedBeneficiary(): SavedBeneficiary {
        val normalizedId = id.takeIf { it.isNotBlank() } ?: beneficiaryAccountId
        val label = nickname?.trim()?.takeIf { it.isNotEmpty() } ?: beneficiaryAccountId
        return SavedBeneficiary(
            id = normalizedId,
            name = label,
            accountId = beneficiaryAccountId
        )
    }

    private fun sanitizeAmountInput(input: String): String {
        val normalized = input
            .replace(',', '.')
            .filter { it.isDigit() || it == '.' }
        if (normalized.isEmpty()) {
            return ""
        }
        val firstDot = normalized.indexOf('.')
        if (firstDot < 0) {
            return normalized
        }
        val integerPart = normalized.substring(0, firstDot)
        val decimalPart = normalized.substring(firstDot + 1).replace(".", "").take(2)
        return if (decimalPart.isEmpty()) {
            "$integerPart."
        } else {
            "$integerPart.$decimalPart"
        }
    }

    private fun parseAmount(value: String): BigDecimal? {
        val candidate = value.trim().removeSuffix(".")
        if (candidate.isBlank()) {
            return null
        }
        val parsed = runCatching {
            BigDecimal(candidate).setScale(2, RoundingMode.HALF_EVEN)
        }.getOrNull() ?: return null
        return parsed.takeIf { it.compareTo(BigDecimal.ZERO) > 0 }
    }

    private fun isContinueEnabled(beneficiary: SavedBeneficiary?, amountInput: String): Boolean {
        return beneficiary != null && parseAmount(amountInput) != null
    }

    private fun buildTransferApi(): TransferApi {
        val baseUrl = resolveBaseUrl()
        if (!BuildConfig.DEBUG && !baseUrl.startsWith("https://")) {
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
            clientBuilder.certificatePinner(buildCertificatePinner(baseUrl))
        }

        val retrofit = Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(clientBuilder.build())
            .addConverterFactory(GsonConverterFactory.create())
            .build()
        return retrofit.create(TransferApi::class.java)
    }

    private fun resolveBaseUrl(): String {
        val raw = if (BuildConfig.DEBUG) {
            BuildConfig.BASE_URL_DEBUG
        } else {
            BuildConfig.BASE_URL_PROD
        }
        return if (raw.endsWith("/")) raw else "$raw/"
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
        pins.forEach { pin -> builder.add(host, pin) }
        return builder.build()
    }

    companion object {
        private const val NETWORK_TIMEOUT_SECONDS = 10L
    }
}

private interface TransferApi {
    @POST("pay/transfer")
    suspend fun transfer(
        @Header("X-Request-Nonce") nonce: String,
        @Body request: TransferRequestDto
    ): Response<TransferResponseDto>
}

private data class TransferRequestDto(
    val fromAccount: String,
    val toAccount: String,
    val amount: BigDecimal,
    val currency: String
)

private data class TransferResponseDto(
    val traceId: String,
    val fromAccount: String,
    val toAccount: String,
    val amount: Double,
    val status: String,
    val fromBalance: Double,
    val toBalance: Double
)
