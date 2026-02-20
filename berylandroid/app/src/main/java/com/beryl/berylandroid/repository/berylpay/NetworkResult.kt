package com.beryl.berylandroid.repository.berylpay

sealed class NetworkResult<out T> {
    data class Success<T>(val data: T) : NetworkResult<T>()
    data class ApiError(val code: Int, val requestId: String? = null) : NetworkResult<Nothing>()
    object NetworkError : NetworkResult<Nothing>()
    object UnknownError : NetworkResult<Nothing>()
}
