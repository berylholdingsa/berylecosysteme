import com.google.cloud.firestore.Firestore
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

interface UserRepository {
    suspend fun getById(uid: String): UserDomain?
    suspend fun upsert(user: UserDomain): UserDomain
}

class FirestoreUserRepository(private val firestore: Firestore) : UserRepository {
    private val collection = firestore.collection("users")

    override suspend fun getById(uid: String): UserDomain? = withContext(Dispatchers.IO) {
        val snapshot = collection.document(uid).get().get()
        if (!snapshot.exists()) return@withContext null

        return@withContext UserDomain(
            uid = uid,
            email = snapshot.getString("email"),
            displayName = snapshot.getString("displayName"),
            createdAt = snapshot.getLong("createdAt") ?: System.currentTimeMillis(),
            updatedAt = snapshot.getLong("updatedAt") ?: System.currentTimeMillis()
        )
    }

    override suspend fun upsert(user: UserDomain): UserDomain = withContext(Dispatchers.IO) {
        val data = mapOf(
            "uid" to user.uid,
            "email" to user.email,
            "displayName" to user.displayName,
            "createdAt" to user.createdAt,
            "updatedAt" to user.updatedAt
        )
        collection.document(user.uid).set(data).get()
        return@withContext user
    }
}
