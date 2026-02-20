package com.beryl.berylandroid.model.kyc

import androidx.annotation.StringRes
import com.beryl.berylandroid.R

enum class KycDocType(val fieldName: String, @StringRes val labelRes: Int) {
    ID("idUrl", R.string.kyc_doc_id),
    SELFIE("selfieUrl", R.string.kyc_doc_selfie),
    ADDRESS("addressUrl", R.string.kyc_doc_address)
}
