package com.beryl.berylandroid.model.community

import com.beryl.berylandroid.model.community.MessageType
import com.beryl.berylandroid.model.community.MessageStatus
import com.beryl.berylandroid.model.community.ConversationCategory

data class Conversation(
    val id: String,
    val name: String,
    val lastMessage: String,
    val lastMessageType: MessageType,
    val timestamp: String,
    val unreadCount: Int,
    val category: ConversationCategory = ConversationCategory.GENERAL,
    val messageStatus: MessageStatus = MessageStatus.SENT,
    val isOnline: Boolean = false,
    val isTyping: Boolean = false
)
