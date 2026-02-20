package com.beryl.berylandroid.network.berylpay

import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Query
import retrofit2.Response

data class BalanceResponseDto(
    val accountId: String,
    val currency: String,
    val balance: Double
)

data class TransactionsResponseDto(
    val accountId: String,
    val transactions: List<TransactionDto>
)

interface LedgerApi {
    @GET("pay/balance")
    suspend fun getBalance(@Query("accountId") accountId: String): Response<BalanceResponseDto>

    @GET("pay/beneficiaries")
    suspend fun getBeneficiaries(): List<BeneficiaryDto>

    @POST("pay/beneficiaries")
    suspend fun saveBeneficiary(@Body request: SaveBeneficiaryRequest)

    @GET("pay/transactions")
    suspend fun getTransactions(
        @Query("page") page: Int = 0,
        @Query("size") size: Int = 20,
        @Query("type") type: String? = null
    ): TransactionsResponseDto
}
