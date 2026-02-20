package com.beryl.berylandroid.ui.community.chat

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AttachFile
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavHostController
import com.beryl.berylandroid.model.community.MessageType
import com.beryl.berylandroid.ui.theme.BerylDarkText
import com.beryl.berylandroid.ui.theme.BerylGreen
import com.beryl.berylandroid.ui.theme.premiumButtonColors
import com.beryl.berylandroid.ui.theme.premiumButtonModifier
import com.beryl.berylandroid.ui.theme.premiumCardBorder
import com.beryl.berylandroid.ui.theme.premiumCardColors
import com.beryl.berylandroid.viewmodel.community.CommunityViewModel
import kotlinx.coroutines.delay
import com.beryl.berylandroid.R

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AttachmentScreen(
    conversationId: String,
    navController: NavHostController,
    viewModel: CommunityViewModel
) {
    var feedback by remember { mutableStateOf<String?>(null) }
    val isDark = isSystemInDarkTheme()
    val feedbackFormat = stringResource(R.string.attachment_feedback_format)
    val attachments = listOf(
        stringResource(R.string.attachment_file_contract),
        stringResource(R.string.attachment_file_pitch),
        stringResource(R.string.attachment_file_esg),
        stringResource(R.string.attachment_file_roadmap)
    )

    LaunchedEffect(feedback) {
        if (feedback != null) {
            delay(1000)
            navController.popBackStack()
        }
    }

    Surface(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        color = Color.Transparent
    ) {
        Column(
            modifier = Modifier.fillMaxSize(),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = stringResource(R.string.attachment_title),
                fontWeight = FontWeight.Bold,
                color = if (isDark) Color.White else MaterialTheme.colorScheme.onBackground,
                fontSize = 22.sp
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = stringResource(R.string.attachment_subtitle),
                color = if (isDark) Color.White else MaterialTheme.colorScheme.onBackground.copy(alpha = 0.8f),
                fontSize = 14.sp
            )
            Spacer(modifier = Modifier.height(16.dp))

            LazyColumn(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                items(attachments) { file ->
                    Card(
                        shape = RoundedCornerShape(16.dp),
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable {
                                feedback = String.format(feedbackFormat, file)
                                viewModel.sendAttachment(MessageType.FILE, conversationId)
                            },
                        elevation = CardDefaults.cardElevation(defaultElevation = if (isDark) 10.dp else 6.dp),
                        colors = premiumCardColors(),
                        border = premiumCardBorder()
                    ) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(16.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(
                                Icons.Default.AttachFile,
                                contentDescription = stringResource(R.string.attachment_file_content_description),
                                tint = MaterialTheme.colorScheme.onBackground
                            )
                            Spacer(modifier = Modifier.width(12.dp))
                            Column(modifier = Modifier.weight(1f)) {
                                Text(
                                    text = file,
                                    fontWeight = FontWeight.SemiBold,
                                    color = if (isDark) Color.White else MaterialTheme.colorScheme.onBackground
                                )
                                Text(
                                    text = stringResource(R.string.attachment_file_size),
                                    fontSize = 12.sp,
                                    color = if (isDark) Color.White else MaterialTheme.colorScheme.onBackground.copy(alpha = 0.75f)
                                )
                            }
                            Button(onClick = {
                                feedback = String.format(feedbackFormat, file)
                                viewModel.sendAttachment(MessageType.FILE, conversationId)
                            },
                                colors = premiumButtonColors(),
                                modifier = premiumButtonModifier()
                            ) {
                                Text(text = stringResource(R.string.action_send))
                            }
                        }
                    }
                }
            }

            AnimatedMessage(feedback = feedback)

            Spacer(modifier = Modifier.height(12.dp))
            TextButton(onClick = { navController.popBackStack() }) {
                Text(text = stringResource(R.string.action_back), color = if (isDark) Color.White else MaterialTheme.colorScheme.onBackground)
            }
        }
    }
}

@Composable
private fun AnimatedMessage(feedback: String?) {
    val isDark = isSystemInDarkTheme()
    AnimatedVisibility(visible = !feedback.isNullOrBlank()) {
        Text(
            text = feedback ?: "",
            color = if (isDark) Color.White else MaterialTheme.colorScheme.onBackground,
            fontWeight = FontWeight.SemiBold,
            modifier = Modifier.padding(vertical = 12.dp)
        )
    }
}
