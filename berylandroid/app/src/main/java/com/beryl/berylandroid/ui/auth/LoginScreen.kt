package com.beryl.berylandroid.ui.auth

import androidx.compose.animation.Crossfade
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.clickable
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material3.*
import androidx.compose.material3.TabRowDefaults.tabIndicatorOffset
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.beryl.berylandroid.ui.common.BerylWallpaperBackground
import com.beryl.berylandroid.ui.theme.BerylDarkBorder
import com.beryl.berylandroid.ui.theme.BerylDarkText
import com.beryl.berylandroid.ui.theme.BerylGreen
import com.beryl.berylandroid.ui.theme.premiumButtonColors
import com.beryl.berylandroid.ui.theme.premiumButtonModifier
import com.beryl.berylandroid.R

// Color Palette
val PremiumGray = Color(0xFF757575)
val DividerGray = Color(0xFFE0E0E0)

@Composable
fun LoginScreen() {
    var selectedTabIndex by remember { mutableIntStateOf(0) }
    var emailOrPhone by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var passwordVisible by remember { mutableStateOf(false) }
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
                    .padding(horizontal = 24.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
            Spacer(modifier = Modifier.height(60.dp))

            // Logo & Title
            Box(
                modifier = Modifier.size(64.dp),
                contentAlignment = Alignment.Center
            ) {
                // Placeholder for Beryl Logo Icon
                Icon(
                    painter = painterResource(id = android.R.drawable.star_big_on), 
                    contentDescription = stringResource(R.string.brand_logo_content_description),
                    modifier = Modifier.size(48.dp),
                    tint = if (isDark) BerylDarkText else BerylGreen
                )
            }
            Text(
                text = stringResource(R.string.app_name),
                fontSize = 28.sp,
                fontWeight = FontWeight.Bold,
                color = if (isDark) BerylDarkText else BerylGreen,
                modifier = Modifier.padding(top = 8.dp)
            )

            Spacer(modifier = Modifier.height(40.dp))

            // Toggle Tab (Email / Phone)
            TabRow(
                selectedTabIndex = selectedTabIndex,
                containerColor = MaterialTheme.colorScheme.background,
                contentColor = BerylGreen,
                indicator = { tabPositions ->
                    if (selectedTabIndex < tabPositions.size) {
                        TabRowDefaults.SecondaryIndicator(
                            Modifier.tabIndicatorOffset(tabPositions[selectedTabIndex]),
                            color = BerylGreen
                        )
                    }
                },
                divider = { HorizontalDivider(color = if (isDark) BerylDarkBorder else DividerGray) }
            ) {
                Tab(
                    selected = selectedTabIndex == 0,
                    onClick = { selectedTabIndex = 0 },
                    text = { Text(stringResource(R.string.email_hint), fontWeight = FontWeight.Medium, color = if (isDark) BerylDarkText else Color.Black) }
                )
                Tab(
                    selected = selectedTabIndex == 1,
                    onClick = { selectedTabIndex = 1 },
                    text = { Text(stringResource(R.string.phone_label), fontWeight = FontWeight.Medium, color = if (isDark) BerylDarkText else Color.Black) }
                )
            }

            Spacer(modifier = Modifier.height(24.dp))

            // Dynamic Input Field
            Crossfade(targetState = selectedTabIndex, label = "InputFade") { index ->
                OutlinedTextField(
                    value = emailOrPhone,
                    onValueChange = { emailOrPhone = it },
                    label = {
                        Text(
                            if (index == 0) {
                                stringResource(R.string.email_address_label)
                            } else {
                                stringResource(R.string.phone_number_label)
                            }
                        )
                    },
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = BerylGreen,
                        focusedLabelColor = BerylGreen,
                        cursorColor = BerylGreen
                    ),
                    keyboardOptions = KeyboardOptions(
                        keyboardType = if (index == 0) KeyboardType.Email else KeyboardType.Phone
                    ),
                    singleLine = true
                )
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Password Field
            OutlinedTextField(
                value = password,
                onValueChange = { password = it },
                label = { Text(stringResource(R.string.password_label)) },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                visualTransformation = if (passwordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                trailingIcon = {
                    val image = if (passwordVisible) Icons.Default.Visibility else Icons.Default.VisibilityOff
                    IconButton(onClick = { passwordVisible = !passwordVisible }) {
                        Icon(
                            imageVector = image,
                            contentDescription = null,
                            tint = if (isDark) BerylDarkText else PremiumGray
                        )
                    }
                },
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = BerylGreen,
                    focusedLabelColor = BerylGreen,
                    cursorColor = BerylGreen
                ),
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                singleLine = true
            )

            Spacer(modifier = Modifier.height(24.dp))

            // Login Button
            Button(
                onClick = { showComingSoon = true },
                shape = RoundedCornerShape(12.dp),
                colors = premiumButtonColors(),
                modifier = premiumButtonModifier(Modifier.fillMaxWidth().height(56.dp))
            ) {
                Text(stringResource(R.string.action_sign_in), color = Color.White, fontSize = 16.sp, fontWeight = FontWeight.Bold)
            }

            Text(
                text = stringResource(R.string.auth_forgot_password),
                color = if (isDark) BerylDarkText else PremiumGray,
                fontSize = 14.sp,
                modifier = Modifier
                    .padding(vertical = 16.dp)
                    .clickable { showComingSoon = true }
            )

            // Divider "OU"
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.padding(vertical = 8.dp)
            ) {
                HorizontalDivider(modifier = Modifier.weight(1f), color = DividerGray)
                Text(
                    text = stringResource(R.string.auth_or),
                    modifier = Modifier.padding(horizontal = 16.dp),
                    color = if (isDark) BerylDarkText else PremiumGray,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold
                )
                HorizontalDivider(modifier = Modifier.weight(1f), color = DividerGray)
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Social Login Buttons
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                OutlinedButton(
                    onClick = { showComingSoon = true },
                    modifier = Modifier.weight(1f).height(50.dp),
                    shape = RoundedCornerShape(12.dp),
                    border = BorderStroke(1.dp, if (isDark) BerylDarkBorder else DividerGray)
                ) {
                    Text(stringResource(R.string.login_google_provider), color = if (isDark) BerylDarkText else Color.Black)
                }
                OutlinedButton(
                    onClick = { showComingSoon = true },
                    modifier = Modifier.weight(1f).height(50.dp),
                    shape = RoundedCornerShape(12.dp),
                    border = BorderStroke(1.dp, if (isDark) BerylDarkBorder else DividerGray)
                ) {
                    Text(stringResource(R.string.login_apple_provider), color = if (isDark) BerylDarkText else Color.Black)
                }
            }

            Spacer(modifier = Modifier.weight(1f))

            // Create Account Button
            OutlinedButton(
                onClick = { showComingSoon = true },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(56.dp)
                    .padding(bottom = 32.dp),
                shape = RoundedCornerShape(12.dp),
                border = BorderStroke(1.5.dp, BerylGreen)
            ) {
                Text(
                    stringResource(R.string.auth_create_new_account),
                    color = if (isDark) BerylDarkText else BerylGreen,
                    fontWeight = FontWeight.Bold
                )
            }
        }
    }
    }
}
