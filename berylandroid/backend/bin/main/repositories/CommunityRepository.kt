import com.google.cloud.firestore.Firestore
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

interface CommunityRepository {
    suspend fun createPost(post: CommunityPostDto): String
    suspend fun getFeed(limit: Int): List<CommunityPostDto>
}

class FirestoreCommunityRepository(private val firestore: Firestore) : CommunityRepository {
    private val collection = firestore.collection("community_posts")

    override suspend fun createPost(post: CommunityPostDto): String = withContext(Dispatchers.IO) {
        val doc = if (post.id.isBlank()) collection.document() else collection.document(post.id)
        val data = mapOf(
            "id" to doc.id,
            "authorUid" to post.authorUid,
            "content" to post.content,
            "tags" to post.tags,
            "createdAt" to post.createdAt
        )
        doc.set(data).get()
        return@withContext doc.id
    }

    override suspend fun getFeed(limit: Int): List<CommunityPostDto> = withContext(Dispatchers.IO) {
        val snapshot = collection.orderBy("createdAt", com.google.cloud.firestore.Query.Direction.DESCENDING)
            .limit(limit.toLong())
            .get()
            .get()

        return@withContext snapshot.documents.map { doc ->
            CommunityPostDto(
                id = doc.getString("id") ?: doc.id,
                authorUid = doc.getString("authorUid") ?: "",
                content = doc.getString("content") ?: "",
                tags = doc.get("tags") as? List<String> ?: emptyList(),
                createdAt = doc.getLong("createdAt") ?: 0L
            )
        }
    }
}
