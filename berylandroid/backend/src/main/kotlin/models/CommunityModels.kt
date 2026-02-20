import kotlinx.serialization.Serializable

@Serializable
data class CommunityPostRequest(
    val content: String,
    val tags: List<String> = emptyList()
)

@Serializable
data class CommunityPostResponse(
    val postId: String,
    val createdAt: Long
)

@Serializable
data class CommunityPostDto(
    val id: String,
    val authorUid: String,
    val content: String,
    val tags: List<String>,
    val createdAt: Long
)

@Serializable
data class CommunityFeedResponse(
    val items: List<CommunityPostDto>
)
