package com.beryl.berylandroid.ui.auth

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
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
import com.beryl.berylandroid.ui.common.BerylWallpaperBackground
import com.beryl.berylandroid.ui.theme.BerylDarkText
import com.beryl.berylandroid.ui.theme.BerylGreen
import com.beryl.berylandroid.ui.theme.premiumButtonColors
import com.beryl.berylandroid.ui.theme.premiumButtonModifier
import com.beryl.berylandroid.R

// Note: To use Icons.Filled.Visibility, you usually need the dependency: 
// implementation("androidx.compose.material:material-icons-extended")
// Since they are unused in AuthScreen and causing unresolved reference errors, they are removed.

@Composable
fun AuthScreen(onLoginClick: () -> Unit) {
    var showComingSoon by remember { mutableStateOf(false) }
    val isDark = isSystemInDarkTheme()
    val comingSoon = stringResource(R.string.coming_soon)
    val actionOk = stringResource(R.string.action_ok)

    if (showComingSoon) {
        AlertDialog(
            onDismissRequest = { showComingSoon = false },
            confirmButton = {
                TextButton(onClick = { showComingSoon = false }) {
                    Text(actionOk)
                }
            },
            title = { Text(comingSoon) },
            text = { Text(comingSoon) }
        )
    }

    BerylWallpaperBackground {
        Surface(
            modifier = Modifier.fillMaxSize(),
            color = Color.Transparent
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(24.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center
            ) {
                Text(
                    text = stringResource(R.string.app_name),
                    fontSize = 32.sp,
                    fontWeight = FontWeight.Bold,
                    color = if (isDark) BerylDarkText else BerylGreen
                )

                Spacer(modifier = Modifier.height(48.dp))

                Button(
                    onClick = onLoginClick,
                    modifier = premiumButtonModifier(Modifier.fillMaxWidth().height(56.dp)),
                    colors = premiumButtonColors(),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Text(stringResource(R.string.action_sign_in), fontSize = 18.sp)
                }

                Spacer(modifier = Modifier.height(16.dp))

                OutlinedButton(
                    onClick = { showComingSoon = true },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(56.dp),
                    border = BorderStroke(1.5.dp, BerylGreen),
                    shape = RoundedCornerShape(12.dp),
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = if (isDark) BerylDarkText else BerylGreen)
                ) {
                    Text(stringResource(R.string.action_sign_up), fontSize = 18.sp)
                }
            }
        }
    }
}
