package com.beryl.berylandroid.ui.community.chat

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsFocusedAsState
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
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Call
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.VideoCall
import androidx.compose.material3.Badge
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Tab
import androidx.compose.material3.TabRow
import androidx.compose.material3.TabRowDefaults
import androidx.compose.material3.TabRowDefaults.tabIndicatorOffset
import androidx.compose.material3.Text
import androidx.compose.material3.TextFieldDefaults
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavHostController
import com.beryl.berylandroid.R
import kotlinx.coroutines.launch
import com.beryl.berylandroid.model.community.CommunityStatus
import com.beryl.berylandroid.model.community.Conversation
import com.beryl.berylandroid.model.community.MessageType
import com.beryl.berylandroid.ui.community.CommunityDestination
import com.beryl.berylandroid.ui.community.safeNavigate
import com.beryl.berylandroid.ui.theme.BerylDarkBorder
import com.beryl.berylandroid.ui.theme.BerylDarkSurface
import com.beryl.berylandroid.ui.theme.BerylDarkSurfaceStrong
import com.beryl.berylandroid.ui.theme.BerylGreen
import com.beryl.berylandroid.ui.theme.premiumCardBorder
import com.beryl.berylandroid.ui.theme.premiumCardColors
import com.beryl.berylandroid.viewmodel.community.CommunityViewModel

private val HomeTabs = listOf(
    R.string.chat_tab_chats,
    R.string.chat_tab_status,
    R.string.chat_tab_calls
)

@Composable
private fun isBerylDarkTheme(): Boolean {
    return MaterialTheme.colorScheme.onBackground == Color.White
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BerylChatHomeScreen(
    navController: NavHostController,
    viewModel: CommunityViewModel
) {
    val conversations by viewModel.prioritizedConversations.collectAsState()
    val statuses by viewModel.statusHighlights.collectAsState()
    val searchQuery by viewModel.searchQuery.collectAsState()
    var selectedTabIndex by rememberSaveable { mutableIntStateOf(0) }
    val snackbarHostState = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()
    val isDark = isBerylDarkTheme()
    val accent = if (isDark) Color.White else BerylGreen
    val mutedAccent = if (isDark) Color.White else BerylGreen.copy(alpha = 0.7f)
    val comingSoon = stringResource(R.string.coming_soon)

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            text = stringResource(R.string.berylcommunity_title),
                            style = MaterialTheme.typography.titleLarge,
                            color = accent,
                            fontWeight = FontWeight.ExtraBold
                        )
                        Text(
                            text = stringResource(R.string.chat_home_subtitle),
                            style = MaterialTheme.typography.labelMedium,
                            color = mutedAccent
                        )
                    }
                },
                actions = {
                    IconButton(onClick = {
                        scope.launch { snackbarHostState.showSnackbar(comingSoon) }
                    }) {
                        Icon(Icons.Default.Search, contentDescription = stringResource(R.string.action_search), tint = accent)
                    }
                    IconButton(onClick = {
                        navController.safeNavigate(CommunityDestination.NewChat.route) {
                            launchSingleTop = true
                        }
                    }) {
                        Icon(Icons.Default.Add, contentDescription = stringResource(R.string.action_new_chat), tint = accent)
                    }
                    IconButton(onClick = {
                        navController.safeNavigate(CommunityDestination.Settings.route) {
                            launchSingleTop = true
                        }
                    }) {
                        Icon(Icons.Default.Settings, contentDescription = stringResource(R.string.action_settings), tint = accent)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface.copy(alpha = if (isDark) 0.92f else 0.78f)
                )
            )
        },
        containerColor = Color.Transparent,
        snackbarHost = { SnackbarHost(snackbarHostState) }
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .background(Color.Transparent)
                .padding(innerPadding)
        ) {
            TabRow(
                selectedTabIndex = selectedTabIndex,
                containerColor = MaterialTheme.colorScheme.surface.copy(alpha = if (isDark) 0.74f else 0.6f),
                contentColor = accent,
                indicator = { tabPositions ->
                    TabRowDefaults.Indicator(
                        modifier = Modifier.tabIndicatorOffset(tabPositions[selectedTabIndex]),
                        color = BerylGreen,
                        height = 3.dp
                    )
                }
            ) {
                HomeTabs.forEachIndexed { index, labelRes ->
                    Tab(
                        selected = selectedTabIndex == index,
                        onClick = { selectedTabIndex = index },
                        text = {
                            Text(
                                text = stringResource(labelRes),
                                fontWeight = if (selectedTabIndex == index) FontWeight.Bold else FontWeight.Medium,
                                color = if (isDark) Color.White else if (selectedTabIndex == index) BerylGreen else BerylGreen.copy(alpha = 0.6f)
                            )
                        }
                    )
                }
            }

            when (selectedTabIndex) {
                0 -> ChatsTab(
                    query = searchQuery,
                    onQueryChange = viewModel::updateSearchQuery,
                    conversations = conversations,
                    onSmartHubClick = {
                        navController.safeNavigate(CommunityDestination.SmartHub.route) {
                            launchSingleTop = true
                        }
                    },
                    onChatClick = { conversation ->
                        viewModel.selectConversation(conversation.id)
                        navController.safeNavigate(CommunityDestination.ChatDetail.createRoute(conversation.id)) {
                            launchSingleTop = true
                        }
                    }
                )
                1 -> StatusTab(statuses = statuses)
                else -> CallsTab(conversations = conversations)
            }
        }
    }
}

@Composable
private fun ChatsTab(
    query: String,
    onQueryChange: (String) -> Unit,
    conversations: List<Conversation>,
    onSmartHubClick: () -> Unit,
    onChatClick: (Conversation) -> Unit
) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(horizontal = 16.dp, vertical = 16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item {
            SmartHubEntryCard(onClick = onSmartHubClick)
        }
        item {
            SearchBar(query = query, onQueryChange = onQueryChange)
        }
        items(conversations, key = { it.id }) { conversation ->
            ChatRow(conversation = conversation, onClick = { onChatClick(conversation) })
        }
    }
}

@Composable
private fun StatusTab(statuses: List<CommunityStatus>) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(horizontal = 16.dp, vertical = 16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        items(statuses, key = { it.id }) { status ->
            StatusRow(status = status)
        }
    }
}

@Composable
private fun CallsTab(conversations: List<Conversation>) {
    val callConversations = conversations.filter {
        it.lastMessageType == MessageType.CALL_AUDIO || it.lastMessageType == MessageType.CALL_VIDEO
    }.ifEmpty { conversations }

    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(horizontal = 16.dp, vertical = 16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        items(callConversations, key = { it.id }) { conversation ->
            CallRow(conversation = conversation)
        }
    }
}

@Composable
private fun SearchBar(query: String, onQueryChange: (String) -> Unit) {
    val interactionSource = remember { MutableInteractionSource() }
    val isFocused by interactionSource.collectIsFocusedAsState()
    val isDark = isBerylDarkTheme()
    val indicatorColor = if (isFocused) {
        if (isDark) Color.White else BerylGreen
    } else {
        if (isDark) BerylDarkBorder else BerylGreen.copy(alpha = 0.4f)
    }
    val indicatorThickness = if (isFocused) 2.dp else 1.dp
    val shape = MaterialTheme.shapes.large
    val focusManager = LocalFocusManager.current

    OutlinedTextField(
        value = query,
        onValueChange = onQueryChange,
        placeholder = {
            Text(text = stringResource(R.string.chat_search_placeholder), color = if (isDark) Color.White else BerylGreen.copy(alpha = 0.6f))
        },
        leadingIcon = {
            Icon(Icons.Default.Search, contentDescription = stringResource(R.string.action_search), tint = if (isDark) Color.White else BerylGreen)
        },
        singleLine = true,
        interactionSource = interactionSource,
        shape = shape,
        keyboardOptions = KeyboardOptions.Default.copy(imeAction = ImeAction.Done),
        keyboardActions = KeyboardActions(onDone = { focusManager.clearFocus() }),
        colors = TextFieldDefaults.colors(
            focusedIndicatorColor = Color.Transparent,
            unfocusedIndicatorColor = Color.Transparent,
            cursorColor = BerylGreen
        ),
        modifier = Modifier
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.surface)
            .border(indicatorThickness, indicatorColor, shape)
    )
}

@Composable
private fun SmartHubEntryCard(onClick: () -> Unit) {
    val isDark = isBerylDarkTheme()
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
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(44.dp)
                    .background(if (isDark) BerylDarkSurfaceStrong else BerylGreen.copy(alpha = 0.15f), CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Icon(imageVector = Icons.Default.Star, contentDescription = null, tint = if (isDark) Color.White else BerylGreen)
            }
            Spacer(modifier = Modifier.size(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = stringResource(R.string.smart_hub_title),
                    color = if (isDark) Color.White else BerylGreen,
                    fontWeight = FontWeight.SemiBold,
                    fontSize = 16.sp
                )
                Text(
                    text = stringResource(R.string.smart_hub_entry_subtitle),
                    color = if (isDark) Color.White else BerylGreen.copy(alpha = 0.75f),
                    fontSize = 13.sp,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
            }
            Text(
                text = stringResource(R.string.action_open),
                color = if (isDark) Color.White else BerylGreen,
                fontWeight = FontWeight.SemiBold,
                fontSize = 13.sp
            )
        }
    }
}

@Composable
private fun ChatRow(conversation: Conversation, onClick: () -> Unit) {
    val isDark = isBerylDarkTheme()
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
            AvatarCircle(label = conversation.name.take(1))
            Spacer(modifier = Modifier.size(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = conversation.name,
                        fontSize = 16.sp,
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
                Badge(containerColor = BerylGreen, contentColor = MaterialTheme.colorScheme.onPrimary) {
                    Text(text = conversation.unreadCount.toString(), fontSize = 12.sp)
                }
            }
        }
    }
}

@Composable
private fun StatusRow(status: CommunityStatus) {
    val isDark = isBerylDarkTheme()
    Card(
        modifier = Modifier.fillMaxWidth(),
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
            AvatarCircle(label = status.owner.take(1), showRing = true)
            Spacer(modifier = Modifier.size(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = status.owner,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.SemiBold,
                    color = if (isDark) Color.White else BerylGreen
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = status.subtitle,
                    fontSize = 13.sp,
                    color = if (isDark) Color.White else BerylGreen.copy(alpha = 0.75f)
                )
            }
            Text(
                text = status.timestamp,
                fontSize = 12.sp,
                color = if (isDark) Color.White else BerylGreen.copy(alpha = 0.7f)
            )
        }
    }
}

@Composable
private fun CallRow(conversation: Conversation) {
    val isVideo = conversation.lastMessageType == MessageType.CALL_VIDEO
    val isDark = isBerylDarkTheme()
    Card(
        modifier = Modifier.fillMaxWidth(),
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
            AvatarCircle(label = conversation.name.take(1))
            Spacer(modifier = Modifier.size(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = conversation.name,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.SemiBold,
                    color = if (isDark) Color.White else BerylGreen
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = if (isVideo) {
                        stringResource(R.string.chat_call_video_label)
                    } else {
                        stringResource(R.string.chat_call_voice_label)
                    },
                    fontSize = 13.sp,
                    color = if (isDark) Color.White else BerylGreen.copy(alpha = 0.75f)
                )
            }
            Text(
                text = conversation.timestamp,
                fontSize = 12.sp,
                color = if (isDark) Color.White else BerylGreen.copy(alpha = 0.7f)
            )
            Spacer(modifier = Modifier.size(12.dp))
            Icon(
                imageVector = if (isVideo) Icons.Default.VideoCall else Icons.Default.Call,
                contentDescription = null,
                tint = if (isDark) Color.White else BerylGreen
            )
        }
    }
}

@Composable
private fun AvatarCircle(label: String, showRing: Boolean = false) {
    val isDark = isBerylDarkTheme()
    Box(
        modifier = Modifier
            .size(48.dp)
            .border(
                width = if (showRing) 2.dp else 0.dp,
                color = if (showRing) if (isDark) Color.White else BerylGreen else Color.Transparent,
                shape = CircleShape
            )
            .background(
                color = if (isDark) BerylDarkSurface else BerylGreen.copy(alpha = 0.12f),
                shape = CircleShape
            ),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = label.uppercase(),
            color = if (isDark) Color.White else BerylGreen,
            fontWeight = FontWeight.SemiBold
        )
    }
}
