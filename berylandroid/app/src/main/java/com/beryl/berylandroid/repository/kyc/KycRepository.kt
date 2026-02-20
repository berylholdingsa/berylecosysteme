package com.beryl.berylandroid.repository.kyc

import android.net.Uri
import com.beryl.berylandroid.model.kyc.KycDocType
import com.beryl.berylandroid.util.awaitResult
import com.google.firebase.storage.FirebaseStorage

class KycRepository(
    private val storage: FirebaseStorage = FirebaseStorage.getInstance()
) {
    suspend fun uploadDocument(uid: String, type: KycDocType, uri: Uri): Result<String> {
        return runCatching {
            val timestamp = System.currentTimeMillis()
            val reference = storage.reference
                .child("kyc/$uid/${type.name.lowercase()}/$timestamp.jpg")
            reference.putFile(uri).awaitResult()
            reference.downloadUrl.awaitResult().toString()
        }
    }
}
