import kotlinx.serialization.Serializable

@Serializable
data class UserDto(
    val uid: String,
    val email: String? = null,
    val displayName: String? = null,
    val createdAt: Long,
    val updatedAt: Long
)

@Serializable
data class UserDomain(
    val uid: String,
    val email: String? = null,
    val displayName: String? = null,
    val createdAt: Long,
    val updatedAt: Long
)
