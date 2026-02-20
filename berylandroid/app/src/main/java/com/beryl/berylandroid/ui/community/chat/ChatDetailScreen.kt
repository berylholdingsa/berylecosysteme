package com.beryl.berylandroid.ui.community.chat

import androidx.compose.foundation.background
import androidx.compose.foundation.isSystemInDarkTheme
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
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Call
import androidx.compose.material.icons.filled.CallEnd
import androidx.compose.material.icons.filled.CameraAlt
import androidx.compose.material.icons.filled.Send
import androidx.compose.material.icons.filled.AttachFile
import androidx.compose.material.icons.filled.Videocam
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavHostController
import com.beryl.berylandroid.model.community.Message
import com.beryl.berylandroid.model.community.MessageType
import com.beryl.berylandroid.ui.community.CommunityDestination
import com.beryl.berylandroid.ui.community.safeNavigate
import com.beryl.berylandroid.ui.theme.BerylDarkSurfaceStrong
import com.beryl.berylandroid.ui.theme.BerylDarkText
import com.beryl.berylandroid.ui.theme.BerylGreen
import com.beryl.berylandroid.ui.theme.premiumButtonColors
import com.beryl.berylandroid.ui.theme.premiumButtonModifier
import com.beryl.berylandroid.viewmodel.community.CommunityViewModel
import java.text.SimpleDateFormat
import java.util.Date
import com.beryl.berylandroid.R

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatDetailScreen(
    conversationId: String,
    navController: NavHostController,
    viewModel: CommunityViewModel
) {
    LaunchedEffect(conversationId) {
        viewModel.selectConversation(conversationId)
    }
    val isDark = isSystemInDarkTheme()
    val conversation by viewModel.selectedConversation.collectAsState(null)
    val messages by viewModel.messagesForSelected.collectAsState(initial = emptyList())
    var messageText by remember { mutableStateOf("") }
    val smartReplies = viewModel.smartReplies

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Transparent)
    ) {
        TopAppBar(
            title = {
                Column {
                    Text(
                        conversation?.name ?: stringResource(R.string.chat_title_default),
                        color = if (isDark) Color.White else MaterialTheme.colorScheme.onBackground
                    )
                    Text(
                        text = when {
                            conversation?.isTyping == true -> stringResource(R.string.chat_status_typing)
                            conversation?.isOnline == true -> stringResource(R.string.chat_status_online)
                            else -> stringResource(R.string.chat_status_offline)
                        },
                        fontSize = 12.sp,
                        color = if (isDark) Color.White else MaterialTheme.colorScheme.onBackground.copy(alpha = 0.75f)
                    )
                }
            },
            colors = TopAppBarDefaults.topAppBarColors(
                containerColor = MaterialTheme.colorScheme.surface.copy(alpha = if (isDark) 0.92f else 0.78f)
            ),
            actions = {
                IconButton(onClick = {
                    navController.safeNavigate(
                        CommunityDestination.Call.createRoute(
                            conversationId = conversationId,
                            callType = MessageType.CALL_AUDIO
                        )
                    )
                }) {
                    Icon(
                        Icons.Default.Call,
                        contentDescription = stringResource(R.string.chat_action_audio_call),
                        tint = if (isDark) Color.White else MaterialTheme.colorScheme.onBackground
                    )
                }
                IconButton(onClick = {
                    navController.safeNavigate(
                        CommunityDestination.Call.createRoute(
                            conversationId = conversationId,
                            callType = MessageType.CALL_VIDEO
                        )
                    )
                }) {
                    Icon(
                        Icons.Default.Videocam,
                        contentDescription = stringResource(R.string.chat_action_video_call),
                        tint = if (isDark) Color.White else MaterialTheme.colorScheme.onBackground
                    )
                }
            }
        )
        LazyColumn(
            modifier = Modifier
                .weight(1f)
                .padding(horizontal = 12.dp),
            reverseLayout = true
        ) {
            items(messages.reversed()) { message ->
                MessageBubble(message = message)
            }
        }
        SmartReplyBar(
            replies = smartReplies,
            onReply = viewModel::sendSmartReply
        )
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            IconButton(onClick = {
                navController.safeNavigate(
                    CommunityDestination.Camera.createRoute(conversationId)
                )
            }) {
                Icon(
                    Icons.Default.CameraAlt,
                    contentDescription = stringResource(R.string.chat_add_image),
                    tint = if (isDark) Color.White else MaterialTheme.colorScheme.onBackground
                )
            }
            IconButton(onClick = {
                navController.safeNavigate(
                    CommunityDestination.Attachment.createRoute(conversationId)
                )
            }) {
                Icon(
                    Icons.Default.AttachFile,
                    contentDescription = stringResource(R.string.chat_add_file),
                    tint = if (isDark) Color.White else MaterialTheme.colorScheme.onBackground
                )
            }
            OutlinedTextField(
                value = messageText,
                onValueChange = { messageText = it },
                modifier = Modifier
                    .weight(1f)
                    .height(56.dp),
                shape = RoundedCornerShape(28.dp),
                placeholder = { Text(stringResource(R.string.chat_input_placeholder)) }
            )
            IconButton(
                onClick = {
                    if (messageText.isNotBlank()) {
                        viewModel.sendTextMessage(messageText, conversationId)
                        messageText = ""
                    }
                }
            ) {
                Icon(
                    Icons.Default.Send,
                    contentDescription = stringResource(R.string.action_send),
                    tint = if (isDark) Color.White else MaterialTheme.colorScheme.onBackground
                )
            }
        }
    }
}

@Composable
private fun MessageBubble(message: Message) {
    val isDark = isSystemInDarkTheme()
    val bubbleColor = if (message.isMine) {
        if (isDark) BerylGreen.copy(alpha = 0.25f) else BerylGreen.copy(alpha = 0.15f)
    } else {
        if (isDark) BerylDarkSurfaceStrong else Color.LightGray
    }
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        horizontalArrangement = if (message.isMine) Arrangement.End else Arrangement.Start
    ) {
        Surface(
            shape = RoundedCornerShape(16.dp),
            color = bubbleColor
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                Text(
                    text = when (message.type) {
                        MessageType.TEXT, MessageType.SMART_REPLY -> message.content
                        MessageType.IMAGE -> stringResource(R.string.chat_message_photo)
                        MessageType.FILE -> stringResource(R.string.chat_message_file)
                        MessageType.VIDEO -> stringResource(R.string.chat_message_video)
                        MessageType.CALL_AUDIO -> stringResource(R.string.chat_message_call_audio)
                        MessageType.CALL_VIDEO -> stringResource(R.string.chat_message_call_video)
                    },
                    color = if (isDark) Color.White else MaterialTheme.colorScheme.onBackground
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = SimpleDateFormat("HH:mm").format(Date(message.timestamp)),
                    fontSize = 10.sp,
                    color = if (isDark) Color.White else MaterialTheme.colorScheme.onBackground.copy(alpha = 0.7f)
                )
            }
        }
    }
}

@Composable
private fun SmartReplyBar(replies: List<String>, onReply: (String) -> Unit) {
    val isDark = isSystemInDarkTheme()
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp)
    ) {
        Text(
            text = stringResource(R.string.chat_smart_reply_title),
            fontWeight = FontWeight.Bold,
            color = if (isDark) Color.White else MaterialTheme.colorScheme.onBackground
        )
        Spacer(modifier = Modifier.height(4.dp))
        Row(
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            replies.forEach { reply ->
                Button(
                    onClick = { onReply(reply) },
                    shape = RoundedCornerShape(20.dp),
                    colors = premiumButtonColors(),
                    modifier = premiumButtonModifier()
                ) {
                    Text(reply, fontSize = 12.sp)
                }
            }
        }
        Spacer(modifier = Modifier.height(8.dp))
        Button(
            onClick = {
                replies.firstOrNull()?.let(onReply)
            },
            shape = RoundedCornerShape(24.dp),
            colors = premiumButtonColors(),
            modifier = premiumButtonModifier()
        ) {
            Text(stringResource(R.string.chat_quick_reply))
        }
    }
}
