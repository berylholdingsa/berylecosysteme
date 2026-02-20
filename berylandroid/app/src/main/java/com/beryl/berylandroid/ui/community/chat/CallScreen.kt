package com.beryl.berylandroid.ui.community.chat

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Call
import androidx.compose.material.icons.filled.Videocam
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.beryl.berylandroid.model.community.MessageType
import com.beryl.berylandroid.ui.theme.BerylDarkText
import com.beryl.berylandroid.ui.theme.BerylGreen
import com.beryl.berylandroid.ui.theme.premiumButtonColors
import com.beryl.berylandroid.ui.theme.premiumButtonModifier
import com.beryl.berylandroid.viewmodel.community.CommunityViewModel
import androidx.navigation.NavHostController
import com.beryl.berylandroid.R

@Composable
fun CallScreen(
    conversationId: String,
    callType: MessageType,
    navController: NavHostController,
    viewModel: CommunityViewModel
) {
    val conversation by viewModel.getConversationAsState(conversationId).collectAsState(initial = null)
    val isDark = isSystemInDarkTheme()
    LaunchedEffect(conversationId, callType) {
        viewModel.recordCallEvent(conversationId, callType)
    }
    Surface(
        modifier = Modifier
            .fillMaxSize(),
        color = Color.Transparent
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Icon(
                imageVector = if (callType == MessageType.CALL_AUDIO) Icons.Default.Call else Icons.Default.Videocam,
                contentDescription = stringResource(R.string.call_content_description),
                tint = MaterialTheme.colorScheme.onBackground,
                modifier = Modifier.size(96.dp)
            )
            Spacer(modifier = Modifier.padding(12.dp))
            Text(
                text = callTypeLabel(callType),
                fontWeight = FontWeight.Bold,
                color = if (isDark) Color.White else MaterialTheme.colorScheme.onBackground,
                fontSize = 22.sp
            )
            Spacer(modifier = Modifier.padding(4.dp))
            Text(
                text = stringResource(
                    R.string.call_with_name_format,
                    conversation?.name ?: stringResource(R.string.brand_name)
                ),
                color = if (isDark) Color.White else MaterialTheme.colorScheme.onBackground.copy(alpha = 0.8f)
            )
            Spacer(modifier = Modifier.padding(24.dp))
            Button(
                onClick = { navController.popBackStack() },
                colors = premiumButtonColors(),
                modifier = premiumButtonModifier()
            ) {
                Text(text = stringResource(R.string.call_hangup), color = MaterialTheme.colorScheme.onPrimary)
            }
        }
    }
}

@Composable
private fun callTypeLabel(callType: MessageType): String = when (callType) {
    MessageType.CALL_AUDIO -> stringResource(R.string.call_type_audio)
    MessageType.CALL_VIDEO -> stringResource(R.string.call_type_video)
    else -> stringResource(R.string.call_type_default)
}
