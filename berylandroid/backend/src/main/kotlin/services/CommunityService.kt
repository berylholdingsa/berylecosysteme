class CommunityService(private val repository: CommunityRepository) {
    suspend fun createPost(authorUid: String, request: CommunityPostRequest): CommunityPostResponse {
        val now = System.currentTimeMillis()
        val post = CommunityPostDto(
            id = "",
            authorUid = authorUid,
            content = request.content,
            tags = request.tags,
            createdAt = now
        )
        val postId = repository.createPost(post)
        return CommunityPostResponse(postId = postId, createdAt = now)
    }

    suspend fun feed(limit: Int): CommunityFeedResponse {
        val items = repository.getFeed(limit)
        return CommunityFeedResponse(items)
    }
}
