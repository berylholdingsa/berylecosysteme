package com.beryl.berylandroid.network.berylpay

import com.google.gson.annotations.SerializedName

data class BeneficiaryDto(
    val id: String = "",
    @SerializedName(value = "beneficiaryAccountId", alternate = ["accountId"])
    val beneficiaryAccountId: String = "",
    val nickname: String? = null,
    val lastUsedAt: String = ""
)

data class SaveBeneficiaryRequest(
    val accountId: String,
    val nickname: String? = null
)
