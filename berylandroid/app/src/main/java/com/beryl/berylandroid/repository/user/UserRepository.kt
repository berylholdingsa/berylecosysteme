package com.beryl.berylandroid.repository.user

import com.beryl.berylandroid.model.auth.KycDocs
import com.beryl.berylandroid.model.auth.KycStatus
import com.beryl.berylandroid.model.auth.UserProfile
import com.beryl.berylandroid.model.auth.UserRole
import com.beryl.berylandroid.model.auth.UserSettings
import com.beryl.berylandroid.model.kyc.KycDocType
import com.beryl.berylandroid.util.awaitResult
import com.google.firebase.auth.FirebaseUser
import com.google.firebase.firestore.DocumentSnapshot
import com.google.firebase.firestore.FirebaseFirestore
import com.google.firebase.firestore.FirebaseFirestoreException
import com.google.firebase.firestore.SetOptions
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlin.math.roundToInt

private const val MAX_FIRESTORE_RISK_SCORE = 100

class UserRepository(
    private val firestore: FirebaseFirestore = FirebaseFirestore.getInstance()
) {
    private val usersCollection = firestore.collection("users")

    fun observeProfile(uid: String): Flow<UserProfile?> = callbackFlow {
        val registration = usersCollection.document(uid).addSnapshotListener { snapshot, error ->
            if (error != null) {
                close(error)
                return@addSnapshotListener
            }
            val profile = snapshot?.toUserProfile()
            trySend(profile).isSuccess
        }
        awaitClose { registration.remove() }
    }

    suspend fun ensureUserProfile(user: FirebaseUser) {
        val docRef = usersCollection.document(user.uid)
        val snapshot = try {
            docRef.get().awaitResult()
        } catch (e: FirebaseFirestoreException) {
            if (e.code == FirebaseFirestoreException.Code.UNAVAILABLE) {
                return
            }
            throw e
        }
        val profile = snapshot.toUserProfile()
        val (firstName, lastName) = extractNames(user.displayName)
        val basePayload = mutableMapOf<String, Any?>(
            "prenom" to firstName,
            "nom" to lastName
        )
        user.email?.takeIf { it.isNotBlank() }?.let { basePayload["email"] = it }
        user.phoneNumber?.takeIf { it.isNotBlank() }?.let { basePayload["phoneNumber"] = it }
        user.photoUrl?.toString()?.takeIf { it.isNotBlank() }?.let { basePayload["photoUrl"] = it }
        if (profile == null) {
            val newProfile = UserProfile(
                uid = user.uid,
                firstName = firstName,
                lastName = lastName,
                email = user.email,
                phoneNumber = user.phoneNumber ?: "",
                photoUrl = user.photoUrl?.toString(),
                createdAt = System.currentTimeMillis()
            )
            docRef.set(newProfile.toMap()).awaitResult()
        } else {
            docRef.set(basePayload, SetOptions.merge()).awaitResult()
            val missingFields = mutableMapOf<String, Any>()
            if (snapshot.getString("kycStatus").isNullOrBlank()) {
                missingFields["kycStatus"] = KycStatus.PENDING.name
            }
            if (snapshot.getString("role").isNullOrBlank()) {
                missingFields["role"] = UserRole.USER.name
            }
            val hasRiskScore =
                snapshot.getDouble("riskScore") != null || snapshot.getLong("riskScore") != null
            if (!hasRiskScore) {
                missingFields["riskScore"] = 0f.toFirestoreRiskScore()
            }
            if (missingFields.isNotEmpty()) {
                docRef.set(missingFields, SetOptions.merge()).awaitResult()
            }
        }
    }

    suspend fun updateProfileFields(uid: String, fields: Map<String, Any?>) {
        usersCollection.document(uid)
            .set(fields, SetOptions.merge())
            .awaitResult()
    }

    suspend fun updateKycDocUrl(uid: String, type: KycDocType, url: String) {
        val path = "kycDocs.${type.fieldName}"
        usersCollection.document(uid)
            .set(mapOf(path to url), SetOptions.merge())
            .awaitResult()
    }

    suspend fun updateKycStatus(uid: String, status: KycStatus, reason: String? = null) {
        val updates = mutableMapOf<String, Any?>(
            "kycStatus" to status.name
        )
        val timestamp = System.currentTimeMillis()
        when (status) {
            KycStatus.PENDING -> {
                updates["kycSubmittedAt"] = timestamp
                updates["kycRejectedAt"] = null
                updates["kycVerifiedAt"] = null
                updates["kycReason"] = null
            }
            KycStatus.VERIFIED -> {
                updates["kycVerifiedAt"] = timestamp
                updates["kycRejectedAt"] = null
            }
            KycStatus.REJECTED -> {
                updates["kycRejectedAt"] = timestamp
                updates["kycReason"] = reason
            }
        }
        usersCollection.document(uid)
            .set(updates, SetOptions.merge())
            .awaitResult()
    }

    private fun DocumentSnapshot.toUserProfile(): UserProfile? {
        if (!exists()) return null
        val settingsMap = get("settings") as? Map<*, *>
        val settings = settingsMap?.toUserSettings() ?: UserSettings()
        return UserProfile(
            uid = getString("uid") ?: id,
            firstName = getString("prenom"),
            lastName = getString("nom"),
            email = getString("email"),
            phoneNumber = getString("phoneNumber"),
            photoUrl = getString("photoUrl"),
            createdAt = getLong("createdAt") ?: 0L,
            kycStatus = getString("kycStatus")?.let { runCatching { KycStatus.valueOf(it) }.getOrDefault(KycStatus.PENDING) }
                ?: KycStatus.PENDING,
            role = getString("role")?.let { runCatching { UserRole.valueOf(it) }.getOrNull() } ?: UserRole.USER,
            riskScore = (get("riskScore") as? Number).toModelRiskScore(),
            kycReason = getString("kycReason"),
            kycSubmittedAt = getLong("kycSubmittedAt"),
            kycVerifiedAt = getLong("kycVerifiedAt"),
            kycRejectedAt = getLong("kycRejectedAt"),
            kycDocs = (get("kycDocs") as? Map<*, *>)?.toKycDocs() ?: KycDocs(),
            settings = settings
        )
    }

    private fun UserProfile.toMap(): Map<String, Any?> {
        return mapOf(
            "uid" to uid,
            "prenom" to firstName,
            "nom" to lastName,
            "email" to email,
            "phoneNumber" to phoneNumber,
            "photoUrl" to photoUrl,
            "createdAt" to createdAt,
            "kycStatus" to kycStatus.name,
            "role" to role.name,
            "riskScore" to riskScore.toFirestoreRiskScore(),
            "kycReason" to kycReason,
            "kycSubmittedAt" to kycSubmittedAt,
            "kycVerifiedAt" to kycVerifiedAt,
            "kycRejectedAt" to kycRejectedAt,
            "kycDocs" to mapOf(
                "idUrl" to kycDocs.idUrl,
                "selfieUrl" to kycDocs.selfieUrl,
                "addressUrl" to kycDocs.addressUrl
            ),
            "settings" to settings.toMap()
        )
    }

    private fun UserSettings.toMap(): Map<String, Any> {
        return mapOf(
            "notificationsEnabled" to notificationsEnabled,
            "theme" to theme,
            "language" to language
        )
    }

    private fun Map<*, *>.toUserSettings(): UserSettings {
        return UserSettings(
            notificationsEnabled = this["notificationsEnabled"] as? Boolean ?: true,
            theme = this["theme"] as? String ?: "system",
            language = this["language"] as? String ?: "fr"
        )
    }

    private fun Map<*, *>.toKycDocs(): KycDocs {
        return KycDocs(
            idUrl = this["idUrl"] as? String,
            selfieUrl = this["selfieUrl"] as? String,
            addressUrl = this["addressUrl"] as? String
        )
    }

    private fun extractNames(displayName: String?): Pair<String?, String?> {
        if (displayName.isNullOrBlank()) return null to null
        val chunks = displayName.trim().split("\\s+".toRegex())
        val firstName = chunks.firstOrNull()?.takeIf { it.isNotBlank() }
        val lastName = chunks.drop(1).joinToString(" ").takeIf { it.isNotBlank() }
        return firstName to lastName
    }
}

private fun Float.toFirestoreRiskScore(): Int {
    val normalized = coerceIn(0f, 1f)
    return (normalized * MAX_FIRESTORE_RISK_SCORE)
        .roundToInt()
        .coerceIn(0, MAX_FIRESTORE_RISK_SCORE)
}

private fun Number?.toModelRiskScore(): Float {
    val value = this?.toFloat() ?: 0f
    return when {
        value > 1f ->
            (value.coerceAtMost(MAX_FIRESTORE_RISK_SCORE.toFloat()) / MAX_FIRESTORE_RISK_SCORE)
                .coerceIn(0f, 1f)
        value < 0f -> 0f
        else -> value
    }
}
