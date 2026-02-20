package com.beryl.berylandroid.model.community

data class Message(
    val id: String,
    val conversationId: String,
    val content: String,
    val timestamp: Long,
    val sender: String,
    val type: MessageType,
    val isMine: Boolean
)
