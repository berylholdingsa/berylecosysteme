package com.beryl.berylandroid.viewmodel.berylpay

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.beryl.berylandroid.repository.berylpay.BerylPayRepository
import com.beryl.berylandroid.repository.berylpay.NetworkResult
import com.beryl.berylandroid.security.DeviceSecurityManager
import com.beryl.berylandroid.session.SessionManager
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

sealed class BerylPayUiState {
    object Loading : BerylPayUiState()
    data class Success(val balance: Double, val currency: String) : BerylPayUiState()
    data class Error(val message: String) : BerylPayUiState()
    object SessionExpired : BerylPayUiState()
}

sealed class BerylPayEvent {
    object NavigateToLogin : BerylPayEvent()
}

class BerylPayViewModel(
    private val repository: BerylPayRepository = BerylPayRepository(),
    private val sessionManager: SessionManager = SessionManager
) : ViewModel() {

    private val _uiState = MutableStateFlow<BerylPayUiState>(BerylPayUiState.Loading)
    val uiState: StateFlow<BerylPayUiState> = _uiState.asStateFlow()
    private val _isRefreshing = MutableStateFlow(false)
    val isRefreshing: StateFlow<Boolean> = _isRefreshing.asStateFlow()
    private val _events = MutableSharedFlow<BerylPayEvent>(extraBufferCapacity = 1)
    val events: SharedFlow<BerylPayEvent> = _events.asSharedFlow()
    private val mutex = Mutex()

    init {
        loadBalance()
    }

    fun loadBalance() {
        loadBalanceInternal(showLoading = true)
    }

    fun refreshBalance() {
        loadBalanceInternal(showLoading = false)
    }

    fun onTransferCompleted() {
        refreshBalance()
    }

    private fun loadBalanceInternal(showLoading: Boolean) {
        viewModelScope.launch {
            if (mutex.isLocked) {
                return@launch
            }
            mutex.withLock {
                try {
                    val token = sessionManager.getToken()
                    val accountId = sessionManager.getAccountId()

                    if (DeviceSecurityManager.shouldBlockForRootRisk()) {
                        _uiState.value = BerylPayUiState.Error(ROOTED_DEVICE_MESSAGE)
                        return@withLock
                    }

                    if (token.isNullOrBlank() || accountId.isNullOrBlank()) {
                        _isRefreshing.value = false
                        _uiState.value = BerylPayUiState.Error(INVALID_SESSION_MESSAGE)
                        _events.emit(BerylPayEvent.NavigateToLogin)
                        return@withLock
                    }

                    if (showLoading) {
                        _uiState.value = BerylPayUiState.Loading
                    } else {
                        _isRefreshing.value = true
                    }

                    _uiState.value = when (val result = repository.fetchBalance(accountId)) {
                        is NetworkResult.Success -> BerylPayUiState.Success(
                            balance = result.data.amount,
                            currency = result.data.currency
                        )
                        is NetworkResult.ApiError -> {
                            if (result.code == SESSION_EXPIRED_CODE) {
                                _events.emit(BerylPayEvent.NavigateToLogin)
                                BerylPayUiState.SessionExpired
                            } else {
                                BerylPayUiState.Error("$DEFAULT_ERROR_MESSAGE (code ${result.code})")
                            }
                        }
                        NetworkResult.NetworkError -> BerylPayUiState.Error(NETWORK_ERROR_MESSAGE)
                        NetworkResult.UnknownError -> BerylPayUiState.Error(DEFAULT_ERROR_MESSAGE)
                    }
                } finally {
                    _isRefreshing.value = false
                }
            }
        }
    }

    companion object {
        private const val SESSION_EXPIRED_CODE = 401
        private const val INVALID_SESSION_MESSAGE = "Session invalide"
        private const val DEFAULT_ERROR_MESSAGE = "Données BerylPay indisponibles."
        private const val NETWORK_ERROR_MESSAGE = "Erreur réseau. Vérifiez votre connexion."
        private const val ROOTED_DEVICE_MESSAGE =
            "Appareil non conforme détecté. Accès BerylPay bloqué pour sécurité."
    }
}
