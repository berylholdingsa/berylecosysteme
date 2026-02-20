package com.beryl.berylandroid.viewmodel.berylpay

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.beryl.berylandroid.network.berylpay.TransactionDto
import com.beryl.berylandroid.repository.berylpay.BerylPayRepository
import com.beryl.berylandroid.repository.berylpay.NetworkResult
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Mutex
import java.time.Instant
import java.util.Locale

enum class TransactionFilter {
    ALL,
    CREDIT,
    DEBIT
}

sealed interface HistoryUiState {
    data object Loading : HistoryUiState
    data class Success(val transactions: List<TransactionDto>) : HistoryUiState
    data object Empty : HistoryUiState
    data class Error(val message: String) : HistoryUiState
}

class TransactionHistoryViewModel(
    private val repository: BerylPayRepository = BerylPayRepository()
) : ViewModel() {

    private val refreshMutex = Mutex()

    private val _transactions = MutableStateFlow<List<TransactionDto>>(emptyList())
    val transactions: StateFlow<List<TransactionDto>> = _transactions.asStateFlow()

    private val _selectedFilter = MutableStateFlow(TransactionFilter.ALL)
    val selectedFilter: StateFlow<TransactionFilter> = _selectedFilter.asStateFlow()

    private val _searchQuery = MutableStateFlow("")
    val searchQuery: StateFlow<String> = _searchQuery.asStateFlow()

    private val _isRefreshing = MutableStateFlow(false)
    val isRefreshing: StateFlow<Boolean> = _isRefreshing.asStateFlow()

    private val _isInitialLoading = MutableStateFlow(true)
    private val _errorMessage = MutableStateFlow<String?>(null)

    val uiState: StateFlow<HistoryUiState> = combine(
        _transactions,
        _selectedFilter,
        _searchQuery,
        _isInitialLoading,
        _errorMessage
    ) { transactions, filter, query, isInitialLoading, errorMessage ->
        val normalizedQuery = query.trim().lowercase(Locale.ROOT)
        val filtered = transactions
            .filter { transaction ->
                when (filter) {
                    TransactionFilter.ALL -> true
                    TransactionFilter.CREDIT -> transaction.type.contains("CREDIT", ignoreCase = true)
                    TransactionFilter.DEBIT -> transaction.type.contains("DEBIT", ignoreCase = true)
                }
            }
            .filter { transaction ->
                if (normalizedQuery.isBlank()) {
                    true
                } else {
                    transaction.type.contains(normalizedQuery, ignoreCase = true) ||
                        transaction.requestId.contains(normalizedQuery, ignoreCase = true) ||
                        transaction.id.contains(normalizedQuery, ignoreCase = true)
                }
            }
            .sortedByDescending { parseTimestamp(it.createdAt) }
        when {
            isInitialLoading && transactions.isEmpty() -> HistoryUiState.Loading
            !errorMessage.isNullOrBlank() && transactions.isEmpty() -> HistoryUiState.Error(errorMessage)
            filtered.isEmpty() -> HistoryUiState.Empty
            else -> HistoryUiState.Success(filtered)
        }
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), HistoryUiState.Loading)

    init {
        refreshTransactions(showInitialLoading = true)
    }

    fun refresh() {
        refreshTransactions(showInitialLoading = false)
    }

    fun onFilterSelected(filter: TransactionFilter) {
        _selectedFilter.value = filter
    }

    fun onSearchQueryChanged(value: String) {
        _searchQuery.value = value
    }

    fun retry() {
        refreshTransactions(showInitialLoading = true)
    }

    private fun refreshTransactions(showInitialLoading: Boolean) {
        viewModelScope.launch {
            if (!refreshMutex.tryLock()) {
                return@launch
            }
            try {
                if (showInitialLoading && _transactions.value.isEmpty()) {
                    _isInitialLoading.value = true
                }
                _isRefreshing.value = true
                _errorMessage.value = null
                when (val result = repository.fetchTransactions()) {
                    is NetworkResult.Success -> {
                        _transactions.value = result.data
                    }
                    else -> {
                        if (_transactions.value.isEmpty()) {
                            _errorMessage.value = errorMessageFor(result)
                        }
                    }
                }
            } finally {
                _isRefreshing.value = false
                _isInitialLoading.value = false
                refreshMutex.unlock()
            }
        }
    }

    private fun errorMessageFor(result: NetworkResult<List<TransactionDto>>): String {
        return when (result) {
            is NetworkResult.ApiError -> "Erreur serveur (${result.code})"
            NetworkResult.NetworkError -> "Erreur réseau. Vérifiez votre connexion."
            NetworkResult.UnknownError -> "Impossible de charger l'historique."
            is NetworkResult.Success -> ""
        }
    }

    private fun parseTimestamp(value: String): Instant {
        return runCatching {
            Instant.parse(value)
        }.getOrElse {
            Instant.EPOCH
        }
    }
}
