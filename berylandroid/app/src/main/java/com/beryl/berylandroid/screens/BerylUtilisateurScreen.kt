package com.beryl.berylandroid.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import com.beryl.berylandroid.R
import com.beryl.berylandroid.navigation.AppRoutes
import com.beryl.berylandroid.ui.theme.BerylDarkBackground
import com.beryl.berylandroid.ui.theme.BerylGreen
import com.beryl.berylandroid.ui.theme.premiumButtonColors
import com.beryl.berylandroid.ui.theme.premiumButtonModifier
import com.beryl.berylandroid.ui.theme.premiumCardBorder
import com.beryl.berylandroid.ui.theme.premiumCardColors
import kotlinx.coroutines.launch

@Composable
fun BerylUtilisateurScreen(navController: NavController) {
    val snackbarHostState = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()
    val isDark = isSystemInDarkTheme()
    val primaryText = MaterialTheme.colorScheme.onBackground
    val secondaryText = MaterialTheme.colorScheme.onBackground.copy(alpha = 0.75f)
    val comingSoonText = stringResource(R.string.coming_soon)

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(if (isDark) BerylDarkBackground else MaterialTheme.colorScheme.background)
            .padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        Text(
            text = stringResource(R.string.user_screen_title),
            fontSize = 22.sp,
            fontWeight = FontWeight.ExtraBold,
            color = MaterialTheme.colorScheme.onBackground
        )

        SnackbarHost(hostState = snackbarHostState)

        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = premiumCardColors(),
            elevation = CardDefaults.cardElevation(defaultElevation = if (isDark) 10.dp else 2.dp),
            border = premiumCardBorder(),
            shape = RoundedCornerShape(16.dp)
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Card(
                    modifier = Modifier.size(56.dp),
                    shape = CircleShape,
                    colors = CardDefaults.cardColors(containerColor = BerylGreen.copy(alpha = 0.1f))
                ) {
                    BoxCenterText(stringResource(R.string.user_initials))
                }
                Spacer(modifier = Modifier.size(12.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = stringResource(R.string.user_display_name_placeholder),
                        fontWeight = FontWeight.SemiBold,
                        color = MaterialTheme.colorScheme.onBackground
                    )
                    Text(
                        text = stringResource(R.string.user_contact_placeholder),
                        color = secondaryText,
                        fontSize = 12.sp
                    )
                }
            }
        }

        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = premiumCardColors(),
            elevation = CardDefaults.cardElevation(defaultElevation = if (isDark) 10.dp else 2.dp),
            border = premiumCardBorder(),
            shape = RoundedCornerShape(16.dp)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Text(
                    text = stringResource(R.string.kyc_title),
                    fontWeight = FontWeight.SemiBold,
                    color = MaterialTheme.colorScheme.onBackground
                )
                Text(
                    text = stringResource(R.string.kyc_status_pending),
                    color = primaryText
                )
                Text(
                    text = stringResource(R.string.kyc_last_update_unknown),
                    color = secondaryText,
                    fontSize = 12.sp
                )
                Button(
                    onClick = { navController.navigate(AppRoutes.Community.PROFILE_KYC) },
                    colors = premiumButtonColors(),
                    modifier = premiumButtonModifier(Modifier.fillMaxWidth())
                ) {
                    Text(text = stringResource(R.string.kyc_verification_action), color = MaterialTheme.colorScheme.onPrimary)
                }
            }
        }

        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = premiumCardColors(),
            elevation = CardDefaults.cardElevation(defaultElevation = if (isDark) 10.dp else 2.dp),
            border = premiumCardBorder(),
            shape = RoundedCornerShape(16.dp)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Text(
                    text = stringResource(R.string.user_actions_title),
                    fontWeight = FontWeight.SemiBold,
                    color = MaterialTheme.colorScheme.onBackground
                )
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Button(
                        onClick = { navController.navigate(AppRoutes.Community.PROFILE_EDIT) },
                        modifier = premiumButtonModifier(Modifier.weight(1f)),
                        colors = premiumButtonColors()
                    ) {
                        Text(text = stringResource(R.string.action_edit_profile), color = MaterialTheme.colorScheme.onPrimary)
                    }
                    Button(
                        onClick = { navController.navigate(AppRoutes.Community.PROFILE_KYC) },
                        modifier = premiumButtonModifier(Modifier.weight(1f)),
                        colors = premiumButtonColors()
                    ) {
                        Text(text = stringResource(R.string.kyc_verification_action), color = MaterialTheme.colorScheme.onPrimary)
                    }
                }
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Button(
                        onClick = { navController.navigate(AppRoutes.Community.PROFILE_SETTINGS) },
                        modifier = premiumButtonModifier(Modifier.weight(1f)),
                        colors = premiumButtonColors()
                    ) {
                        Text(text = stringResource(R.string.action_settings), color = MaterialTheme.colorScheme.onPrimary)
                    }
                    Button(
                        onClick = {
                            scope.launch { snackbarHostState.showSnackbar(comingSoonText) }
                        },
                        modifier = premiumButtonModifier(Modifier.weight(1f)),
                        colors = premiumButtonColors()
                    ) {
                        Text(text = stringResource(R.string.action_logout), color = MaterialTheme.colorScheme.onPrimary)
                    }
                }
            }
        }
    }
}

@Composable
private fun BoxCenterText(text: String) {
    Column(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(text = text, color = MaterialTheme.colorScheme.onBackground, fontWeight = FontWeight.Bold)
    }
}
