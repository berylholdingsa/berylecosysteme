package com.beryl.berylandroid.ui.community.chat

import androidx.compose.foundation.background
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Call
import androidx.compose.material.icons.filled.CreditCard
import androidx.compose.material.icons.filled.DirectionsCar
import androidx.compose.material.icons.filled.Star
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavHostController
import com.beryl.berylandroid.model.community.Conversation
import com.beryl.berylandroid.model.community.MessageType
import com.beryl.berylandroid.model.community.SuperAppModule
import com.beryl.berylandroid.ui.community.CommunityDestination
import com.beryl.berylandroid.ui.community.safeNavigate
import com.beryl.berylandroid.ui.theme.BerylDarkSurface
import com.beryl.berylandroid.ui.theme.BerylDarkSurfaceStrong
import com.beryl.berylandroid.ui.theme.BerylGreen
import com.beryl.berylandroid.ui.theme.premiumCardBorder
import com.beryl.berylandroid.ui.theme.premiumCardColors
import com.beryl.berylandroid.viewmodel.community.CommunityViewModel
import kotlinx.coroutines.launch
import com.beryl.berylandroid.R
import java.util.Locale

private data class ReminderItem(
    val id: String,
    val title: String,
    val detail: String,
    val time: String,
    val conversationId: String
)

private data class ShortcutItem(
    val id: String,
    val title: String,
    val subtitle: String,
    val icon: ImageVector,
    val module: SuperAppModule? = null,
    val conversationId: String? = null
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SmartHubScreen(
    navController: NavHostController,
    viewModel: CommunityViewModel
) {
    val conversations by viewModel.prioritizedConversations.collectAsState()
    val insights by viewModel.aiInsights.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()
    val followUpFormat = stringResource(R.string.smart_hub_follow_up_format)
    val replyFormat = stringResource(R.string.smart_hub_reply_format)
    val shortcutPay = stringResource(R.string.smart_hub_shortcut_pay)
    val shortcutMove = stringResource(R.string.smart_hub_shortcut_move)
    val shortcutCall = stringResource(R.string.smart_hub_shortcut_call)
    val callSubtitleFormat = stringResource(R.string.smart_hub_call_subtitle_format)
    val comingSoon = stringResource(R.string.coming_soon)

    val importantChats = remember(conversations) {
        conversations.sortedWith(
            compareByDescending<Conversation> { it.unreadCount }
                .thenByDescending { it.isTyping }
                .thenByDescending { it.isOnline }
        ).take(3)
    }

    val reminders = remember(conversations, insights) {
        val insightReminders = insights.mapNotNull { insight ->
            val conversation = conversations.firstOrNull { it.id == insight.conversationId } ?: return@mapNotNull null
            ReminderItem(
                id = insight.id,
                title = String.format(Locale.getDefault(), followUpFormat, conversation.name),
                detail = insight.highlightMessage,
                time = conversation.timestamp,
                conversationId = conversation.id
            )
        }
        val fallbackReminders = conversations.take(4).map { conversation ->
            ReminderItem(
                id = "reminder_${conversation.id}",
                title = String.format(Locale.getDefault(), replyFormat, conversation.name),
                detail = conversation.lastMessage,
                time = conversation.timestamp,
                conversationId = conversation.id
            )
        }
        (insightReminders + fallbackReminders)
            .distinctBy { it.id }
            .take(4)
    }

    val shortcuts = remember(conversations, viewModel.superAppLinks) {
        val callTarget = conversations.firstOrNull()
        buildList {
            val payLink = viewModel.superAppLinks.firstOrNull { it.module == SuperAppModule.BERYLPAY }
            val moveLink = viewModel.superAppLinks.firstOrNull { it.module == SuperAppModule.MOBILITE }
            if (payLink != null) {
                add(
                    ShortcutItem(
                        id = payLink.id,
                        title = shortcutPay,
                        subtitle = payLink.title,
                        icon = Icons.Default.CreditCard,
                        module = payLink.module
                    )
                )
            }
            if (moveLink != null) {
                add(
                    ShortcutItem(
                        id = moveLink.id,
                        title = shortcutMove,
                        subtitle = moveLink.title,
                        icon = Icons.Default.DirectionsCar,
                        module = moveLink.module
                    )
                )
            }
            if (callTarget != null) {
                add(
                    ShortcutItem(
                        id = "call_${callTarget.id}",
                        title = shortcutCall,
                        subtitle = String.format(Locale.getDefault(), callSubtitleFormat, callTarget.name),
                        icon = Icons.Default.Call,
                        conversationId = callTarget.id
                    )
                )
            }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = stringResource(R.string.smart_hub_title),
                        color = if (isSystemInDarkTheme()) Color.White else BerylGreen,
                        fontWeight = FontWeight.SemiBold
                    )
                },
                navigationIcon = {
                    IconButton(onClick = { navController.popBackStack() }) {
                        Icon(
                            imageVector = Icons.Default.ArrowBack,
                            contentDescription = stringResource(R.string.action_back),
                            tint = if (isSystemInDarkTheme()) Color.White else BerylGreen
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface.copy(
                        alpha = if (isSystemInDarkTheme()) 0.92f else 0.78f
                    )
                )
            )
        },
        containerColor = Color.Transparent,
        snackbarHost = { SnackbarHost(snackbarHostState) }
    ) { innerPadding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .background(Color.Transparent)
                .padding(innerPadding),
            contentPadding = PaddingValues(horizontal = 16.dp, vertical = 16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            item {
                SmartHubHero()
            }
            item {
                SectionTitle(title = stringResource(R.string.smart_hub_section_important))
            }
            items(importantChats, key = { it.id }) { conversation ->
                ImportantChatCard(
                    conversation = conversation,
                    onClick = {
                        navController.safeNavigate(CommunityDestination.ChatDetail.createRoute(conversation.id)) {
                            launchSingleTop = true
                        }
                    }
                )
            }
            item {
                SectionTitle(title = stringResource(R.string.smart_hub_section_reminders))
            }
            items(reminders, key = { it.id }) { reminder ->
                ReminderCard(
                    reminder = reminder,
                    onClick = {
                        navController.safeNavigate(CommunityDestination.ChatDetail.createRoute(reminder.conversationId)) {
                            launchSingleTop = true
                        }
                    }
                )
            }
            item {
                SectionTitle(title = stringResource(R.string.smart_hub_section_shortcuts))
            }
            item {
                LazyRow(
                    contentPadding = PaddingValues(horizontal = 4.dp),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    items(shortcuts, key = { it.id }) { shortcut ->
                        ShortcutCard(
                            shortcut = shortcut,
                            onClick = {
                                if (shortcut.conversationId != null) {
                                    navController.safeNavigate(
                                        CommunityDestination.Call.createRoute(shortcut.conversationId, MessageType.CALL_AUDIO)
                                    ) {
                                        launchSingleTop = true
                                    }
                                } else {
                                    scope.launch { snackbarHostState.showSnackbar(comingSoon) }
                                }
                            }
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun SmartHubHero() {
    val isDark = isSystemInDarkTheme()
    Card(
        colors = premiumCardColors(),
        elevation = CardDefaults.cardElevation(defaultElevation = if (isDark) 8.dp else 0.dp),
        border = premiumCardBorder()
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(52.dp)
                    .background(if (isDark) BerylDarkSurfaceStrong else BerylGreen.copy(alpha = 0.2f), CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Icon(imageVector = Icons.Default.Star, contentDescription = null, tint = if (isDark) Color.White else BerylGreen)
            }
            Spacer(modifier = Modifier.size(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = stringResource(R.string.smart_hub_hero_title),
                    color = if (isDark) Color.White else BerylGreen,
                    fontWeight = FontWeight.SemiBold,
                    fontSize = 16.sp
                )
                Text(
                    text = stringResource(R.string.smart_hub_hero_subtitle),
                    color = if (isDark) Color.White else BerylGreen.copy(alpha = 0.75f),
                    fontSize = 13.sp
                )
            }
        }
    }
}

@Composable
private fun SectionTitle(title: String) {
    val isDark = isSystemInDarkTheme()
    Text(
        text = title,
        style = MaterialTheme.typography.titleMedium,
        color = if (isDark) Color.White else BerylGreen,
        fontWeight = FontWeight.SemiBold
    )
}

@Composable
private fun ImportantChatCard(conversation: Conversation, onClick: () -> Unit) {
    val isDark = isSystemInDarkTheme()
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        colors = premiumCardColors(),
        elevation = CardDefaults.cardElevation(defaultElevation = if (isDark) 8.dp else 1.dp),
        border = premiumCardBorder()
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(14.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(44.dp)
                    .background(if (isDark) BerylDarkSurface else BerylGreen.copy(alpha = 0.12f), CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = conversation.name.take(1).uppercase(),
                    color = if (isDark) Color.White else BerylGreen,
                    fontWeight = FontWeight.SemiBold
                )
            }
            Spacer(modifier = Modifier.size(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = conversation.name,
                        fontSize = 15.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = if (isDark) Color.White else BerylGreen
                    )
                    Spacer(modifier = Modifier.weight(1f))
                    Text(
                        text = conversation.timestamp,
                        fontSize = 12.sp,
                        color = if (isDark) Color.White else BerylGreen.copy(alpha = 0.7f)
                    )
                }
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = conversation.lastMessage,
                    fontSize = 13.sp,
                    color = if (isDark) Color.White else BerylGreen.copy(alpha = 0.75f),
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
            }
            if (conversation.unreadCount > 0) {
                Spacer(modifier = Modifier.size(12.dp))
                Box(
                    modifier = Modifier
                        .background(BerylGreen, CircleShape)
                        .padding(horizontal = 8.dp, vertical = 4.dp)
                ) {
                    Text(
                        text = conversation.unreadCount.toString(),
                        color = MaterialTheme.colorScheme.onPrimary,
                        fontSize = 12.sp
                    )
                }
            }
        }
    }
}

@Composable
private fun ReminderCard(reminder: ReminderItem, onClick: () -> Unit) {
    val isDark = isSystemInDarkTheme()
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        colors = premiumCardColors(),
        elevation = CardDefaults.cardElevation(defaultElevation = if (isDark) 8.dp else 1.dp),
        border = premiumCardBorder()
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(14.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .background(if (isDark) BerylDarkSurfaceStrong else BerylGreen.copy(alpha = 0.1f), CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Icon(imageVector = Icons.Default.Star, contentDescription = null, tint = if (isDark) Color.White else BerylGreen)
            }
            Spacer(modifier = Modifier.size(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = reminder.title,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.SemiBold,
                    color = if (isDark) Color.White else BerylGreen
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = reminder.detail,
                    fontSize = 13.sp,
                    color = if (isDark) Color.White else BerylGreen.copy(alpha = 0.75f),
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis
                )
            }
            Text(
                text = reminder.time,
                fontSize = 12.sp,
                color = if (isDark) Color.White else BerylGreen.copy(alpha = 0.7f)
            )
        }
    }
}

@Composable
private fun ShortcutCard(shortcut: ShortcutItem, onClick: () -> Unit) {
    val isDark = isSystemInDarkTheme()
    Card(
        modifier = Modifier
            .size(width = 190.dp, height = 120.dp)
            .clickable(onClick = onClick),
        colors = premiumCardColors(),
        elevation = CardDefaults.cardElevation(defaultElevation = if (isDark) 8.dp else 1.dp),
        border = premiumCardBorder()
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(14.dp),
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            Box(
                modifier = Modifier
                    .size(36.dp)
                    .background(if (isDark) BerylDarkSurfaceStrong else BerylGreen.copy(alpha = 0.15f), CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Icon(imageVector = shortcut.icon, contentDescription = null, tint = if (isDark) Color.White else BerylGreen)
            }
            Column {
                Text(
                    text = shortcut.title,
                    fontWeight = FontWeight.SemiBold,
                    color = if (isDark) Color.White else BerylGreen,
                    fontSize = 14.sp
                )
                Text(
                    text = shortcut.subtitle,
                    color = if (isDark) Color.White else BerylGreen.copy(alpha = 0.75f),
                    fontSize = 12.sp,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis
                )
            }
        }
    }
}
