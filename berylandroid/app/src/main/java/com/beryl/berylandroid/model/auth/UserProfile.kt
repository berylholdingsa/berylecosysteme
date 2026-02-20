package com.beryl.berylandroid.model.auth

data class UserSettings(
    val notificationsEnabled: Boolean = true,
    val theme: String = "system",
    val language: String = "fr"
)

enum class KycStatus {
    PENDING,
    VERIFIED,
    REJECTED
}

enum class UserRole {
    USER,
    MERCHANT,
    DRIVER
}

data class KycDocs(
    val idUrl: String? = null,
    val selfieUrl: String? = null,
    val addressUrl: String? = null
) {
    val completed: Boolean
        get() = !idUrl.isNullOrBlank() && !selfieUrl.isNullOrBlank() && !addressUrl.isNullOrBlank()
}

data class UserProfile(
    val uid: String,
    val firstName: String?,
    val lastName: String?,
    val email: String?,
    val phoneNumber: String?,
    val photoUrl: String?,
    val createdAt: Long,
    val kycStatus: KycStatus = KycStatus.PENDING,
    val role: UserRole = UserRole.USER,
    val riskScore: Float = 0f,
    val kycReason: String? = null,
    val kycSubmittedAt: Long? = null,
    val kycVerifiedAt: Long? = null,
    val kycRejectedAt: Long? = null,
    val kycDocs: KycDocs = KycDocs(),
    val settings: UserSettings = UserSettings()
) {
    val fullName: String?
        get() {
            return listOfNotNull(firstName?.takeIf { it.isNotBlank() }, lastName?.takeIf { it.isNotBlank() })
                .takeIf { it.isNotEmpty() }
                ?.joinToString(" ")
        }
}
