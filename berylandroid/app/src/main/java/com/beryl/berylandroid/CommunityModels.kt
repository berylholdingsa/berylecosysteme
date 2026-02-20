package com.beryl.berylandroid

import com.google.firebase.Timestamp

enum class MessageType {
    TEXT, IMAGE, VIDEO, SYSTEM
}

data class UserProfile(
    val uid: String = "",
    val displayName: String = "",
    val email: String = "",
    val photoUrl: String = "",
    val isPremium: Boolean = false
)

data class Message(
    val id: String = "",
    val senderId: String = "",
    val senderName: String = "",
    val content: String = "",
    val timestamp: Timestamp = Timestamp.now(),
    val type: MessageType = MessageType.TEXT
)

data class Conversation(
    val id: String = "",
    val participants: List<String> = emptyList(),
    val lastMessage: String = "",
    val lastUpdate: Timestamp = Timestamp.now(),
    val title: String = ""
)
