package com.beryl.esg.ui.state

sealed interface ESGUiState<out T> {
    data object Loading : ESGUiState<Nothing>
    data object Empty : ESGUiState<Nothing>
    data class Error(val code: String) : ESGUiState<Nothing>
    data class Content<T>(val data: T) : ESGUiState<T>
}
