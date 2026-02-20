package com.beryl.berylandroid

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.google.firebase.auth.FirebaseAuth
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

class CommunityViewModel(
    private val repository: CommunityRepository = CommunityRepository()
) : ViewModel() {

    private val auth = FirebaseAuth.getInstance()
    private var conversationsJob: Job? = null
    private var messagesJob: Job? = null

    data class CommunityUiState(
        val isLoading: Boolean = false,
        val userProfile: UserProfile? = null,
        val conversations: List<Conversation> = emptyList(),
        val selectedConversationMessages: List<Message> = emptyList(),
        val error: String? = null
    )

    private val _uiState = MutableStateFlow(CommunityUiState())
    val uiState: StateFlow<CommunityUiState> = _uiState.asStateFlow()

    /**
     * Appelé quand l'utilisateur est authentifié.
     * Initialise le profil et commence l'écoute des conversations si un UID est présent.
     */
    fun onUserAuthenticated() {
        val uid = auth.currentUser?.uid
        if (uid != null) {
            loadUserProfile(uid)
            startListeningConversations(uid)
        } else {
            _uiState.update { it.copy(error = "Utilisateur non authentifié") }
        }
    }

    private fun loadUserProfile(uid: String) {
        viewModelScope.launch {
            val profile = repository.getUserProfile(uid)
            _uiState.update { it.copy(userProfile = profile) }
        }
    }

    private fun startListeningConversations(uid: String) {
        conversationsJob?.cancel()
        _uiState.update { it.copy(isLoading = true) }
        conversationsJob = repository.getConversations(uid)
            .onEach { conversations ->
                _uiState.update { it.copy(conversations = conversations, isLoading = false) }
            }
            .catch { e ->
                _uiState.update { it.copy(error = e.localizedMessage, isLoading = false) }
            }
            .launchIn(viewModelScope)
    }

    fun selectConversation(conversationId: String) {
        messagesJob?.cancel()
        messagesJob = repository.getMessages(conversationId)
            .onEach { messages ->
                _uiState.update { it.copy(selectedConversationMessages = messages) }
            }
            .catch { e ->
                _uiState.update { it.copy(error = e.localizedMessage) }
            }
            .launchIn(viewModelScope)
    }

    fun sendMessage(conversationId: String, content: String) {
        val uid = auth.currentUser?.uid ?: return
        val profile = _uiState.value.userProfile
        
        viewModelScope.launch {
            val message = Message(
                senderId = uid,
                senderName = profile?.displayName ?: "Anonyme",
                content = content
            )
            try {
                repository.sendMessage(conversationId, message)
            } catch (e: Exception) {
                _uiState.update { it.copy(error = e.localizedMessage) }
            }
        }
    }

    fun stopListening() {
        conversationsJob?.cancel()
        messagesJob?.cancel()
    }

    override fun onCleared() {
        super.onCleared()
        stopListening()
    }
}
