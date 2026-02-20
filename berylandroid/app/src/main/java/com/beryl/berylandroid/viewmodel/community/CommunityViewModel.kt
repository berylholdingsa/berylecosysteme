package com.beryl.berylandroid.viewmodel.community

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.beryl.berylandroid.BuildConfig
import com.beryl.berylandroid.model.community.AiInsight
import com.beryl.berylandroid.model.community.CommunityGroup
import com.beryl.berylandroid.model.community.CommunityRole
import com.beryl.berylandroid.model.community.CommunityStatus
import com.beryl.berylandroid.model.community.Conversation
import com.beryl.berylandroid.model.community.ConversationCategory
import com.beryl.berylandroid.model.community.Message
import com.beryl.berylandroid.model.community.MessageStatus
import com.beryl.berylandroid.model.community.MessageType
import com.beryl.berylandroid.model.community.SuperAppLink
import com.beryl.berylandroid.model.community.SuperAppModule
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.debounce
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.util.UUID
import kotlin.math.max
import kotlin.math.min
import android.util.Log

class CommunityViewModel : ViewModel() {
    companion object {
        private const val USER_CONVERSATION_ID = "self"
        private const val LOG_TAG = "CommunityViewModel"
        private const val MIN_DEBOUNCE_MS = 0L
        private const val MAX_DEBOUNCE_MS = 2_000L

        internal fun clampDebounceMs(value: Long): Long {
            return max(MIN_DEBOUNCE_MS, min(value, MAX_DEBOUNCE_MS))
        }
    }

    private val filterCategories = listOf(
        ConversationCategory.GENERAL,
        ConversationCategory.AMIS,
        ConversationCategory.BUSINESS,
        ConversationCategory.MOBILITE,
        ConversationCategory.PAIEMENTS,
        ConversationCategory.ESG
    )

    private val initialConversations = listOf(
        Conversation(
            id = "amina",
            name = "Amina",
            lastMessage = "Salut, on finalise le deal aujourd'hui ?",
            lastMessageType = MessageType.TEXT,
            timestamp = "12:04",
            unreadCount = 2,
            category = ConversationCategory.AMIS,
            messageStatus = MessageStatus.READ,
            isOnline = true,
            isTyping = false
        ),
        Conversation(
            id = "koffi",
            name = "Koffi",
            lastMessage = "Tu as vu le nouveau modèle ?",
            lastMessageType = MessageType.IMAGE,
            timestamp = "11:58",
            unreadCount = 1,
            category = ConversationCategory.BUSINESS,
            messageStatus = MessageStatus.DELIVERED,
            isOnline = true,
            isTyping = true
        ),
        Conversation(
            id = "support",
            name = "Béryl Support",
            lastMessage = "Votre compte a été mis à jour.",
            lastMessageType = MessageType.TEXT,
            timestamp = "10:22",
            unreadCount = 1,
            category = ConversationCategory.ESG,
            messageStatus = MessageStatus.READ,
            isOnline = false,
            isTyping = false
        ),
        Conversation(
            id = "mariam",
            name = "Mariam",
            lastMessage = "On se voit à 16h ?",
            lastMessageType = MessageType.TEXT,
            timestamp = "09:30",
            unreadCount = 0,
            category = ConversationCategory.AMIS,
            messageStatus = MessageStatus.READ,
            isOnline = false,
            isTyping = false
        ),
        Conversation(
            id = "mobilite",
            name = "Équipe Mobilité",
            lastMessage = "Nouveau véhicule ajouté.",
            lastMessageType = MessageType.TEXT,
            timestamp = "08:15",
            unreadCount = 3,
            category = ConversationCategory.MOBILITE,
            messageStatus = MessageStatus.DELIVERED,
            isOnline = true,
            isTyping = false
        ),
        Conversation(
            id = "berylpay",
            name = "Équipe BérylPay",
            lastMessage = "Votre transfert de 2 250 € est prêt.",
            lastMessageType = MessageType.FILE,
            timestamp = "07:40",
            unreadCount = 0,
            category = ConversationCategory.PAIEMENTS,
            messageStatus = MessageStatus.SENT,
            isOnline = true,
            isTyping = false
        )
    )

    private val statusHighlightsSeed = listOf(
        CommunityStatus("status_you", "Vous", "Touchez pour ajouter un statut", "Maintenant", 0f, isNew = false),
        CommunityStatus("status_amila", "Amina", "Statut Mobilité — 24h", "Il y a 2 h", 0.64f, conversationId = "amina"),
        CommunityStatus("status_mobi", "Mobilité premium", "Trajet planifié pour 18h", "Il y a 1 h", 0.78f, conversationId = "mobilite"),
        CommunityStatus("status_esg", "Impact Béryl", "Rapport ESG prêt", "Il y a 3 h", 0.35f, conversationId = "support")
    )

    private val groupsSeed = listOf(
        CommunityGroup("group_mobility", "Club Mobilité Béryl", CommunityRole.ADMIN, 18, "Aujourd'hui • 08:42", 3),
        CommunityGroup("group_business", "Béryl Business", CommunityRole.MEMBER, 12, "Aujourd'hui • 09:15", 1),
        CommunityGroup("group_impact", "Communauté ESG", CommunityRole.ADMIN, 24, "Hier • 18:10", 0)
    )

    private val insightsSeed = listOf(
        AiInsight(
            id = "insight_summary",
            title = "Résumé intelligent",
            summary = "Amina veut finaliser la proposition, transférer le dossier et confirmer la signature avant 17h.",
            highlightMessage = "Décision finale attendue aujourd'hui",
            conversationId = "amina"
        ),
        AiInsight(
            id = "insight_key_message",
            title = "Message clé",
            summary = "Koffi a partagé une vidéo de cockpit, il faut un retour express pour débloquer la production.",
            highlightMessage = "Préparer le feedback design",
            conversationId = "koffi"
        )
    )

    private val _conversations = MutableStateFlow(initialConversations)
    private val _messages = MutableStateFlow(
        initialConversations.associate { conv ->
            conv.id to listOf(
                Message(
                    id = UUID.randomUUID().toString(),
                    conversationId = conv.id,
                    content = conv.lastMessage,
                    timestamp = System.currentTimeMillis(),
                    sender = conv.name,
                    type = conv.lastMessageType,
                    isMine = false
                )
            )
        }
    )
    private val _searchQuery = MutableStateFlow("")
    private val debounceDurationMs = clampDebounceMs(BuildConfig.SEARCH_DEBOUNCE_MS).also { clamped ->
        if (BuildConfig.DEBUG && clamped != BuildConfig.SEARCH_DEBOUNCE_MS) {
            Log.w(
                LOG_TAG,
                "SEARCH_DEBOUNCE_MS clamped from ${BuildConfig.SEARCH_DEBOUNCE_MS}ms to ${clamped}ms."
            )
        }
    }
    private val debouncedSearchQuery = _searchQuery
        .debounce(debounceDurationMs)
        .stateIn(viewModelScope, SharingStarted.Eagerly, _searchQuery.value)
    private val _selectedConversationId = MutableStateFlow(initialConversations.first().id)
    private val _activeFilter = MutableStateFlow(filterCategories.first())
    private val _lastNotification = MutableStateFlow<String?>(null)
    private val _statusHighlights = MutableStateFlow(statusHighlightsSeed)
    private val _communityGroups = MutableStateFlow(groupsSeed)
    private val _aiInsights = MutableStateFlow(insightsSeed)

    val searchQuery: StateFlow<String> = _searchQuery.asStateFlow()
    val lastNotification: StateFlow<String?> = _lastNotification.asStateFlow()
    val activeFilter: StateFlow<ConversationCategory> = _activeFilter.asStateFlow()
    val statusHighlights: StateFlow<List<CommunityStatus>> = _statusHighlights.asStateFlow()
    val communityGroups: StateFlow<List<CommunityGroup>> = _communityGroups.asStateFlow()
    val aiInsights: StateFlow<List<AiInsight>> = _aiInsights.asStateFlow()
    val superAppLinks = listOf(
        SuperAppLink("link_mobility", "Trajets premium", "Réservez un chauffeur dédié, suivez chaque étape.", SuperAppModule.MOBILITE),
        SuperAppLink("link_payments", "BérylPay", "Gérez vos transferts instantanément et sécurisez les signatures.", SuperAppModule.BERYLPAY),
        SuperAppLink("link_impact", "Impact & ESG", "Découvrez les communautés à impact et rejoignez les initiatives.", SuperAppModule.ESG)
    )
    val filterCategoriesList = filterCategories
    val smartReplies = listOf("À tout de suite", "Je regarde ça", "Merci, on valide", "Je vous partage l'update")

    val filteredConversations: StateFlow<List<Conversation>> = combine(_conversations, debouncedSearchQuery) { conversations, query ->
        if (query.isBlank()) {
            conversations
        } else {
            val normalizedQuery = query.trim()
            conversations.filter {
                it.name.contains(normalizedQuery, ignoreCase = true) ||
                    it.lastMessage.contains(normalizedQuery, ignoreCase = true)
            }
        }
    }.stateIn(viewModelScope, SharingStarted.Eagerly, _conversations.value)

    val prioritizedConversations: StateFlow<List<Conversation>> = combine(filteredConversations, _activeFilter) { conversations, filter ->
        conversations.sortedWith(compareByDescending<Conversation> {
            val anticipationScore = if (it.category == filter) 20 else 0
            val typingScore = if (it.isTyping) 5 else 0
            val unreadScore = it.unreadCount * 3
            anticipationScore + typingScore + unreadScore
        }.thenByDescending {
            if (it.isOnline) 1 else 0
        })
    }.stateIn(viewModelScope, SharingStarted.Eagerly, filteredConversations.value)

    val selectedConversation: StateFlow<Conversation?> = combine(_conversations, _selectedConversationId) { conversations, selectedId ->
        conversations.firstOrNull { it.id == selectedId }
    }.stateIn(viewModelScope, SharingStarted.Eagerly, _conversations.value.firstOrNull())

    val messagesForSelected: StateFlow<List<Message>> = combine(_messages, _selectedConversationId) { map, selectedId ->
        selectedId?.let { map[it] } ?: emptyList()
    }.stateIn(viewModelScope, SharingStarted.Eagerly, emptyList())

    fun updateSearchQuery(query: String) {
        _searchQuery.value = query
    }

    fun updateActiveFilter(category: ConversationCategory) {
        _activeFilter.value = category
    }

    fun markStatusViewed(statusId: String) {
        _statusHighlights.update { statuses ->
            statuses.map { status ->
                if (status.id == statusId) status.copy(isNew = false) else status
            }
        }
    }

    fun toggleGroupRole(groupId: String) {
        _communityGroups.update { groups ->
            groups.map { group ->
                if (group.id == groupId) {
                    val newRole = if (group.role == CommunityRole.ADMIN) CommunityRole.MEMBER else CommunityRole.ADMIN
                    group.copy(role = newRole)
                } else group
            }
        }
    }

    fun selectConversation(id: String) {
        _selectedConversationId.value = id
        _conversations.update { conversations ->
            conversations.map { conv ->
                if (conv.id == id) conv.copy(unreadCount = 0) else conv
            }
        }
    }

    fun sendTextMessage(text: String, conversationId: String) {
        appendMessage(
            conversationId = conversationId,
            message = buildMessage(text, conversationId, isMine = true, MessageType.TEXT)
        )
        simulateIncomingConversationMessage(conversationId)
    }

    fun sendSmartReply(text: String) {
        val conversationId = _selectedConversationId.value ?: return
        appendMessage(
            conversationId = conversationId,
            message = buildMessage(text, conversationId, isMine = true, MessageType.SMART_REPLY)
        )
        simulateIncomingConversationMessage(conversationId)
    }

    fun sendAttachment(type: MessageType, conversationId: String) {
        val content = when (type) {
            MessageType.IMAGE -> "Photo partagée"
            MessageType.FILE -> "Document envoyé"
            MessageType.VIDEO -> "Vidéo rapidement sourcée"
            else -> "Pièce jointe"
        }
        appendMessage(
            conversationId = conversationId,
            message = buildMessage(content, conversationId, isMine = true, type)
        )
    }

    fun recordCallEvent(conversationId: String, callType: MessageType) {
        val content = when (callType) {
            MessageType.CALL_AUDIO -> "Appel audio premium"
            MessageType.CALL_VIDEO -> "Appel vidéo premium"
            else -> "Appel Béryl"
        }
        appendMessage(
            conversationId = conversationId,
            message = buildMessage(content, conversationId, isMine = true, callType)
        )
    }

    fun createConversation(name: String): String {
        val id = UUID.randomUUID().toString()
        val conversation = Conversation(
            id = id,
            name = name,
            lastMessage = "Nouvelle discussion",
            lastMessageType = MessageType.TEXT,
            timestamp = "Maintenant",
            unreadCount = 0,
            category = ConversationCategory.GENERAL
        )
        _conversations.update { it + conversation }
        _messages.update { map ->
            map + (id to listOf())
        }
        selectConversation(id)
        return id
    }

    fun getConversationAsState(conversationId: String): StateFlow<Conversation?> {
        return _conversations
            .map { conversations -> conversations.firstOrNull { it.id == conversationId } }
            .stateIn(viewModelScope, SharingStarted.Eagerly, null)
    }

    fun clearNotification() {
        _lastNotification.value = null
    }

    fun updateCurrentUserName(firstName: String?) {
        val normalized = firstName?.trim()?.takeIf { it.isNotBlank() }
        _conversations.update { conversations ->
            val withoutUser = conversations.filter { it.id != USER_CONVERSATION_ID }
            if (normalized == null) {
                withoutUser
            } else {
                buildList {
                    add(buildUserConversation(normalized))
                    addAll(withoutUser)
                }
            }
        }
        _messages.update { existing ->
            val cleared = existing - USER_CONVERSATION_ID
            normalized?.let {
                cleared + (USER_CONVERSATION_ID to buildUserMessages(it))
            } ?: cleared
        }
    }

    private fun buildUserConversation(firstName: String): Conversation {
        return Conversation(
            id = USER_CONVERSATION_ID,
            name = firstName,
            lastMessage = "Vous êtes connecté·e sur Béryl",
            lastMessageType = MessageType.TEXT,
            timestamp = "Maintenant",
            unreadCount = 0,
            category = ConversationCategory.GENERAL,
            messageStatus = MessageStatus.READ,
            isOnline = true,
            isTyping = false
        )
    }

    private fun buildUserMessages(firstName: String) = listOf(
        Message(
            id = UUID.randomUUID().toString(),
            conversationId = USER_CONVERSATION_ID,
            content = "Bonjour $firstName !",
            timestamp = System.currentTimeMillis(),
            sender = firstName,
            type = MessageType.TEXT,
            isMine = true
        )
    )

    private fun appendMessage(conversationId: String, message: Message) {
        _messages.update { map ->
            val messages = map[conversationId].orEmpty() + message
            map + (conversationId to messages)
        }
        _conversations.update { conversations ->
            conversations.map { conv ->
                if (conv.id == conversationId) {
                    val nextStatus = if (message.isMine) MessageStatus.SENT else MessageStatus.READ
                    conv.copy(
                        lastMessage = message.content,
                        timestamp = currentTimeStamp(),
                        unreadCount = if (message.isMine) 0 else conv.unreadCount + 1,
                        messageStatus = nextStatus
                    )
                } else conv
            }
        }
    }

    private fun simulateIncomingConversationMessage(conversationId: String) {
        viewModelScope.launch {
            delay(1200)
            val reply = Message(
                id = UUID.randomUUID().toString(),
                conversationId = conversationId,
                content = "Réponse automatique Béryl",
                timestamp = System.currentTimeMillis(),
                sender = "Béryl AI",
                type = MessageType.TEXT,
                isMine = false
            )
            appendMessage(conversationId, reply)
            _conversations.update { conversations ->
                conversations.map { conv ->
                    if (conv.id == conversationId) {
                        conv.copy(
                            unreadCount = if (_selectedConversationId.value == conversationId) 0 else conv.unreadCount + 1,
                            lastMessage = reply.content,
                            timestamp = currentTimeStamp(),
                            messageStatus = MessageStatus.READ
                        )
                    } else conv
                }
            }
            _lastNotification.value = "Nouveau message de ${reply.sender}"
        }
    }

    private fun buildMessage(content: String, conversationId: String, isMine: Boolean, type: MessageType): Message {
        return Message(
            id = UUID.randomUUID().toString(),
            conversationId = conversationId,
            content = content,
            timestamp = System.currentTimeMillis(),
            sender = if (isMine) "Vous" else "Béryl",
            type = type,
            isMine = isMine
        )
    }

    private fun currentTimeStamp(): String {
        return java.text.SimpleDateFormat("HH:mm").format(System.currentTimeMillis())
    }
}
