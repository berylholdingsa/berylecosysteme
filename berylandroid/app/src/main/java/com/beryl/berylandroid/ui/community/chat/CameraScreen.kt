package com.beryl.berylandroid.ui.community.chat

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.animateContentSize
import androidx.compose.foundation.background
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavHostController
import com.beryl.berylandroid.model.community.MessageType
import com.beryl.berylandroid.ui.theme.BerylDarkSurfaceStrong
import com.beryl.berylandroid.ui.theme.BerylDarkText
import com.beryl.berylandroid.ui.theme.BerylGreen
import com.beryl.berylandroid.ui.theme.premiumButtonColors
import com.beryl.berylandroid.ui.theme.premiumButtonModifier
import com.beryl.berylandroid.viewmodel.community.CommunityViewModel
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CameraAlt
import com.beryl.berylandroid.R

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CameraScreen(
    conversationId: String,
    navController: NavHostController,
    viewModel: CommunityViewModel
) {
    var captured by remember { mutableStateOf(false) }
    val isDark = isSystemInDarkTheme()
    val statusText = if (captured) {
        stringResource(R.string.camera_status_captured)
    } else {
        stringResource(R.string.camera_status_ready)
    }

    LaunchedEffect(captured) {
        if (captured) {
            viewModel.sendAttachment(MessageType.IMAGE, conversationId)
        }
    }

    Surface(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        color = Color.Transparent
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .animateContentSize(),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Box(
                modifier = Modifier
                    .size(160.dp)
                    .shadow(12.dp, CircleShape)
                    .background(
                        if (isDark) BerylDarkSurfaceStrong else BerylGreen.copy(alpha = 0.1f),
                        CircleShape
                    ),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Default.CameraAlt,
                    contentDescription = stringResource(R.string.camera_content_description),
                    tint = if (isDark) BerylDarkText else BerylGreen,
                    modifier = Modifier.size(72.dp)
                )
            }
            Spacer(modifier = Modifier.height(12.dp))
            Text(
                text = stringResource(R.string.camera_title),
                fontSize = 24.sp,
                color = if (isDark) Color.White else MaterialTheme.colorScheme.onBackground
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = statusText,
                color = if (isDark) Color.White else MaterialTheme.colorScheme.onBackground.copy(alpha = 0.8f),
                fontSize = 14.sp
            )
            Spacer(modifier = Modifier.height(24.dp))
            Button(
                onClick = { captured = true },
                shape = CircleShape,
                modifier = premiumButtonModifier(Modifier.height(52.dp)),
                colors = premiumButtonColors()
            ) {
                Text(
                    text = if (captured) {
                        stringResource(R.string.camera_action_captured)
                    } else {
                        stringResource(R.string.camera_action_capture)
                    }
                )
            }
            Spacer(modifier = Modifier.height(12.dp))
            AnimatedVisibility(visible = captured) {
                Row(
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = stringResource(R.string.camera_sharing),
                        color = if (isDark) Color.White else MaterialTheme.colorScheme.onBackground.copy(alpha = 0.8f),
                        fontSize = 14.sp
                    )
                    TextButton(onClick = { navController.popBackStack() }) {
                        Text(
                            text = stringResource(R.string.camera_back_to_chat),
                            color = if (isDark) Color.White else MaterialTheme.colorScheme.onBackground
                        )
                    }
                }
            }
            Spacer(modifier = Modifier.weight(1f))
            TextButton(onClick = { navController.popBackStack() }) {
                Text(
                    text = stringResource(R.string.action_cancel),
                    color = if (isDark) Color.White else MaterialTheme.colorScheme.onBackground
                )
            }
        }
    }
}
