import io.ktor.util.AttributeKey


data class AuthenticatedUser(
    val uid: String,
    val email: String? = null,
    val name: String? = null,
    val emailVerified: Boolean = false
)

val AuthenticatedUserKey = AttributeKey<AuthenticatedUser>("authenticatedUser")
