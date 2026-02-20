package com.beryl.berylandroid.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Send
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.beryl.berylandroid.model.auth.KycStatus
import com.beryl.berylandroid.model.auth.UserProfile
import com.beryl.berylandroid.model.auth.toSentinelUserContextOrDefault
import com.beryl.berylandroid.ui.theme.BerylDarkSurfaceStrong
import com.beryl.berylandroid.ui.theme.BerylDarkText
import com.beryl.berylandroid.ui.theme.BerylGreen
import com.beryl.berylandroid.viewmodel.auth.UserViewModel
import com.beryl.sentinel.sdk.SentinelClient
import com.beryl.sentinel.sdk.SentinelUserContext
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Date
import java.util.UUID
import com.beryl.berylandroid.R

@Composable
fun ChatScreen(sentinelClient: SentinelClient) {
    val isDark = isSystemInDarkTheme()
    val scope = rememberCoroutineScope()
    val userViewModel: UserViewModel = viewModel()
    val userProfile by userViewModel.currentUserProfile.collectAsState()
    val sentinelContext = userProfile.toSentinelUserContextOrDefault()
    val welcomeMessage = stringResource(R.string.chat_welcome_message)
    val userSenderLabel = stringResource(R.string.chat_sender_you)
    val sentinelSenderLabel = stringResource(R.string.chat_sender_sentinel)
    val blockedMessage = stringResource(R.string.chat_blocked_message)
    val sendFailedMessage = stringResource(R.string.chat_send_failed)
    var inputText by remember { mutableStateOf("") }
    var messages by remember { mutableStateOf(sampleMessages(welcomeMessage, sentinelSenderLabel)) }
    val listState = rememberLazyListState()

    LaunchedEffect(messages.size) {
        if (messages.isNotEmpty()) {
            listState.animateScrollToItem(messages.lastIndex)
        }
    }

    Column(modifier = Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background)) {
        LazyColumn(
            modifier = Modifier
                .weight(1f)
                .padding(horizontal = 16.dp, vertical = 12.dp),
            state = listState,
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            items(messages) { message ->
                MessageBubble(message) {
                    scope.launch {
                        sendMessage(
                            messages,
                            it,
                            sentinelClient,
                            sentinelContext,
                            userProfile,
                            onMessages = { updated -> messages = updated },
                            userSenderLabel = userSenderLabel,
                            sentinelSenderLabel = sentinelSenderLabel,
                            blockedMessage = blockedMessage,
                            sendFailedMessage = sendFailedMessage
                        )
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(8.dp))
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            val sendMessage = {
                if (inputText.isNotBlank()) {
                    scope.launch {
                        val content = inputText.trim()
                        inputText = ""
                        sendMessage(
                            messages,
                            content,
                            sentinelClient,
                            sentinelContext,
                            userProfile,
                            onMessages = { updated -> messages = updated },
                            userSenderLabel = userSenderLabel,
                            sentinelSenderLabel = sentinelSenderLabel,
                            blockedMessage = blockedMessage,
                            sendFailedMessage = sendFailedMessage
                        )
                    }
                }
            }
            OutlinedTextField(
                value = inputText,
                onValueChange = { inputText = it },
                modifier = Modifier.weight(1f),
                placeholder = { Text(stringResource(R.string.chat_input_placeholder)) },
                singleLine = true,
                shape = RoundedCornerShape(24.dp),
                keyboardOptions = KeyboardOptions.Default.copy(imeAction = ImeAction.Done),
                keyboardActions = KeyboardActions(onDone = { sendMessage() })
            )
            IconButton(
                onClick = {
                    sendMessage()
                }
            ) {
            Icon(
                Icons.Default.Send,
                contentDescription = stringResource(R.string.action_send),
                tint = MaterialTheme.colorScheme.onBackground
            )
        }
    }
}
}

private suspend fun sendMessage(
    currentMessages: List<ChatMessage>,
    content: String,
    sentinelClient: SentinelClient,
    userContext: SentinelUserContext,
    userProfile: UserProfile?,
    onMessages: (List<ChatMessage>) -> Unit,
    userSenderLabel: String,
    sentinelSenderLabel: String,
    blockedMessage: String,
    sendFailedMessage: String
) {
    val userMessage = ChatMessage(
        id = UUID.randomUUID().toString(),
        text = content,
        sender = userSenderLabel,
        timestamp = System.currentTimeMillis(),
        isUser = true
    )
    val interim = currentMessages + userMessage
    onMessages(interim)

    val kycStatus = userProfile?.kycStatus ?: KycStatus.PENDING
    val riskScore = userProfile?.riskScore ?: 0f
    val response = runCatching { sentinelClient.sendMessage(content, userContext) }
    val responseMessage = response.fold(
        onSuccess = { resp ->
            if (shouldBlockIntent(resp.intent, riskScore)) {
                ChatMessage(
                    id = UUID.randomUUID().toString(),
                    text = blockedMessage,
                    sender = sentinelSenderLabel,
                    timestamp = System.currentTimeMillis(),
                    isUser = false
                )
            } else {
                ChatMessage(
                    id = UUID.randomUUID().toString(),
                    text = resp.result,
                    sender = sentinelSenderLabel,
                    timestamp = System.currentTimeMillis(),
                    isUser = false,
                    actions = filterActionsForKyc(resp.actions, kycStatus)
                )
            }
        },
        onFailure = {
            ChatMessage(
                id = UUID.randomUUID().toString(),
                text = sendFailedMessage,
                sender = sentinelSenderLabel,
                timestamp = System.currentTimeMillis(),
                isUser = false
            )
        }
    )
    onMessages(interim + responseMessage)
}

@Composable
private fun MessageBubble(message: ChatMessage, onAction: (String) -> Unit) {
    val isDark = isSystemInDarkTheme()
    val bubbleColor = if (message.isUser) {
        if (isDark) BerylGreen.copy(alpha = 0.25f) else Color(0xFFDCF8C6)
    } else {
        if (isDark) BerylDarkSurfaceStrong else Color(0xFFF2F2F2)
    }
    Column(horizontalAlignment = if (message.isUser) Alignment.End else Alignment.Start) {
        Surface(
            shape = RoundedCornerShape(16.dp),
            color = bubbleColor,
            tonalElevation = 1.dp,
            shadowElevation = 0.dp
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                Text(
                    text = message.text,
                    fontSize = 16.sp,
                    color = MaterialTheme.colorScheme.onBackground
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = SimpleDateFormat("HH:mm").format(Date(message.timestamp)),
                    fontSize = 10.sp,
                    color = MaterialTheme.colorScheme.onBackground.copy(alpha = 0.7f)
                )
            }
        }
        if (message.actions.isNotEmpty()) {
            Row(
                modifier = Modifier
                    .horizontalScroll(rememberScrollState())
                    .padding(top = 6.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                message.actions.forEach { action ->
                    TextButton(onClick = { onAction(action) }) {
                        Text(text = action, color = MaterialTheme.colorScheme.onBackground)
                    }
                }
            }
        }
    }
}

private data class ChatMessage(
    val id: String,
    val text: String,
    val sender: String,
    val timestamp: Long,
    val isUser: Boolean,
    val actions: List<String> = emptyList()
)

private fun sampleMessages(welcomeMessage: String, sentinelSenderLabel: String) = listOf(
    ChatMessage(
        id = UUID.randomUUID().toString(),
        text = welcomeMessage,
        sender = sentinelSenderLabel,
        timestamp = System.currentTimeMillis(),
        isUser = false
    )
)

private const val HIGH_RISK_THRESHOLD = 0.75f
private val sensitiveIntents = setOf(
    "payment.transfer",
    "payment.withdraw",
    "account.delete",
    "wallet.payout"
)

private fun shouldBlockIntent(intent: String, riskScore: Float): Boolean {
    return riskScore >= HIGH_RISK_THRESHOLD && intent in sensitiveIntents
}

private fun filterActionsForKyc(actions: List<String>, kycStatus: KycStatus): List<String> {
    return if (kycStatus == KycStatus.VERIFIED) actions else emptyList()
}
