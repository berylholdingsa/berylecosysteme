package com.beryl.berylandroid

import com.google.firebase.firestore.FirebaseFirestore
import com.google.firebase.firestore.Query
import com.google.firebase.firestore.ListenerRegistration
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.tasks.await

class CommunityRepository {
    private val firestore = FirebaseFirestore.getInstance()

    suspend fun getUserProfile(uid: String): UserProfile? {
        return try {
            firestore.collection("users").document(uid).get().await().toObject(UserProfile::class.java)
        } catch (e: Exception) {
            null
        }
    }

    fun getConversations(userId: String): Flow<List<Conversation>> = callbackFlow {
        val subscription = firestore.collection("conversations")
            .whereArrayContains("participants", userId)
            .orderBy("lastUpdate", Query.Direction.DESCENDING)
            .addSnapshotListener { snapshot, error ->
                if (error != null) {
                    close(error)
                    return@addSnapshotListener
                }
                val conversations = snapshot?.documents?.mapNotNull { it.toObject(Conversation::class.java)?.copy(id = it.id) } ?: emptyList()
                trySend(conversations)
            }
        awaitClose { subscription.remove() }
    }

    fun getMessages(conversationId: String): Flow<List<Message>> = callbackFlow {
        val subscription = firestore.collection("conversations")
            .document(conversationId)
            .collection("messages")
            .orderBy("timestamp", Query.Direction.ASCENDING)
            .addSnapshotListener { snapshot, error ->
                if (error != null) {
                    close(error)
                    return@addSnapshotListener
                }
                val messages = snapshot?.documents?.mapNotNull { it.toObject(Message::class.java)?.copy(id = it.id) } ?: emptyList()
                trySend(messages)
            }
        awaitClose { subscription.remove() }
    }

    suspend fun sendMessage(conversationId: String, message: Message) {
        firestore.collection("conversations")
            .document(conversationId)
            .collection("messages")
            .add(message)
            .await()
        
        firestore.collection("conversations")
            .document(conversationId)
            .update("lastMessage", message.content, "lastUpdate", message.timestamp)
            .await()
    }
}
