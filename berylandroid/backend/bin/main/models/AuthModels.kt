import kotlinx.serialization.Serializable

@Serializable
data class AuthVerifyRequest(
    val idToken: String
)

@Serializable
data class AuthVerifyResponse(
    val uid: String,
    val email: String? = null,
    val name: String? = null,
    val emailVerified: Boolean
)
