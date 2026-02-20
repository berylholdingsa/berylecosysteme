package com.beryl.berylandroid.screens

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.ExperimentalAnimationApi
import androidx.compose.animation.core.MutableTransitionState
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.RadioButtonUnchecked
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.beryl.berylandroid.R
import com.beryl.berylandroid.model.auth.KycStatus
import com.beryl.berylandroid.model.kyc.KycDocType
import com.beryl.berylandroid.navigation.AppRoutes
import com.beryl.berylandroid.ui.theme.BerylDarkBackground
import com.beryl.berylandroid.ui.theme.BerylDarkText
import com.beryl.berylandroid.ui.theme.BerylGreen
import com.beryl.berylandroid.ui.theme.premiumButtonColors
import com.beryl.berylandroid.ui.theme.premiumButtonModifier
import com.beryl.berylandroid.ui.theme.premiumCardBorder
import com.beryl.berylandroid.ui.theme.premiumCardColors
import com.beryl.berylandroid.viewmodel.profile.ProfileViewModel
import androidx.navigation.NavHostController
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

private val PendingBannerColor = Color(0xFFFFC107)
private val RejectedColor = Color(0xFFD32F2F)

@OptIn(ExperimentalAnimationApi::class)
@Composable
fun ProfileScreen(
    navController: NavHostController,
    onSignOut: () -> Unit,
    viewModel: ProfileViewModel = viewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }
    val transitionState =
        remember { MutableTransitionState(false).apply { targetState = true } }
    var isEditing by remember { mutableStateOf(false) }
    val context = LocalContext.current
    val isActivityHost = context is android.app.Activity
    val idLauncher =
        if (isActivityHost) {
            rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
                uri?.let { viewModel.uploadDocument(KycDocType.ID, it) }
            }
        } else null
    val selfieLauncher =
        if (isActivityHost) {
            rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
                uri?.let { viewModel.uploadDocument(KycDocType.SELFIE, it) }
            }
        } else null
    val addressLauncher =
        if (isActivityHost) {
            rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
                uri?.let { viewModel.uploadDocument(KycDocType.ADDRESS, it) }
            }
        } else null

    fun pickDocument(type: KycDocType) {
        when (type) {
            KycDocType.ID -> idLauncher?.launch("image/*")
            KycDocType.SELFIE -> selfieLauncher?.launch("image/*")
            KycDocType.ADDRESS -> addressLauncher?.launch("image/*")
        }
    }

    LaunchedEffect(uiState.snackbarMessage) {
        uiState.snackbarMessage?.let {
            snackbarHostState.showSnackbar(it)
            viewModel.clearSnackbar()
        }
    }

    Scaffold(
        containerColor = Color.Transparent,
        snackbarHost = { SnackbarHost(snackbarHostState) }
    ) { padding ->
        Surface(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding),
            color = Color.Transparent
        ) {
            if (uiState.isLoading) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator(color = BerylGreen)
                }
                return@Surface
            }

            AnimatedVisibility(
                visibleState = transitionState,
                enter = fadeIn(),
                exit = fadeOut()
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .verticalScroll(rememberScrollState())
                        .padding(24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    val onSave = {
                        viewModel.saveProfile()
                        isEditing = false
                    }
                    UserHeader(
                        state = uiState,
                        isEditing = isEditing,
                        onEdit = { isEditing = true }
                    )
                    ProfileForm(uiState, isEditing, viewModel, onSave)
                    val validationMessage = uiState.validationMessage
                    if (!validationMessage.isNullOrBlank()) {
                        Text(
                            text = validationMessage,
                            color = Color.Red,
                            fontSize = 12.sp
                        )
                    }
                    KycSection(
                        uiState = uiState,
                        onKycVerification = { navController.navigate(AppRoutes.Community.KYC) }
                    )
                    KycDocumentsSection(
                        uiState = uiState,
                        onSubmit = viewModel::submitKyc,
                        onRetry = viewModel::retryKyc,
                        pickDocument = ::pickDocument
                    )
                    SecuritySection(uiState)
                    ActionButtonsSection(
                        onEditProfile = { navController.navigate(AppRoutes.Community.EDIT_PROFILE) },
                        onSettings = { navController.navigate(AppRoutes.Community.SETTINGS) },
                        onSignOut = onSignOut
                    )
                }
            }
        }
    }
}

@Composable
private fun UserHeader(
    state: ProfileViewModel.ProfileUiState,
    isEditing: Boolean,
    onEdit: () -> Unit
) {
    val isDark = isSystemInDarkTheme()
    val titleColor = Color.White
    val secondaryText = Color.White
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = if (isDark) 10.dp else 4.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF014421)),
        border = premiumCardBorder()
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(Color(0xFF014421))
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text(
                text = stringResource(R.string.user_screen_title),
                fontSize = 22.sp,
                fontWeight = FontWeight.ExtraBold,
                color = titleColor
            )
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Surface(
                    modifier = Modifier.size(64.dp),
                    shape = CircleShape,
                    color = BerylGreen.copy(alpha = 0.1f)
                ) {
                    Box(
                        modifier = Modifier.fillMaxSize(),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = state.firstName?.firstOrNull()?.uppercaseChar()?.toString()
                                ?: stringResource(R.string.user_initial_single),
                            fontSize = 28.sp,
                            fontWeight = FontWeight.Black,
                            color = titleColor
                        )
                    }
                }
                Spacer(modifier = Modifier.size(12.dp))
                Column(
                    modifier = Modifier.weight(1f)
                ) {
                    Text(
                        text = listOfNotNull(
                            state.firstName?.takeIf { it.isNotBlank() },
                            state.lastName?.takeIf { it.isNotBlank() }
                        ).joinToString(" ").ifBlank { stringResource(R.string.user_display_name_placeholder) },
                        fontWeight = FontWeight.Bold,
                        fontSize = 18.sp,
                        color = titleColor
                    )
                    Text(
                        text = listOfNotNull(
                            state.email.takeIf { it.isNotBlank() },
                            state.phoneNumber.takeIf { it.isNotBlank() }
                        ).ifEmpty { listOf(stringResource(R.string.user_contact_placeholder)) }.joinToString(" · "),
                        fontSize = 14.sp,
                        color = secondaryText
                    )
                }
            }
            Button(
                onClick = onEdit,
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color.White,
                    contentColor = Color(0xFF014421)
                ),
                modifier = premiumButtonModifier(),
                shape = RoundedCornerShape(12.dp),
                border = BorderStroke(2.dp, Color(0xFF014421))
            ) {
                Text(text = stringResource(R.string.action_edit_profile), color = Color(0xFF014421))
            }
        }
    }
}

@Composable
private fun ProfileForm(
    state: ProfileViewModel.ProfileUiState,
    isEditing: Boolean,
    viewModel: ProfileViewModel,
    onSave: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.surface),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            OutlinedTextField(
                value = state.firstName,
                onValueChange = viewModel::onFirstNameChange,
                modifier = Modifier.weight(1f),
                label = { Text(stringResource(R.string.profile_first_name_label)) },
                enabled = isEditing
            )
            OutlinedTextField(
                value = state.lastName,
                onValueChange = viewModel::onLastNameChange,
                modifier = Modifier.weight(1f),
                label = { Text(stringResource(R.string.profile_last_name_label)) },
                enabled = isEditing
            )
        }
        OutlinedTextField(
            value = state.email,
            onValueChange = viewModel::onEmailChange,
            modifier = Modifier.fillMaxWidth(),
            label = { Text(stringResource(R.string.email_hint)) },
            enabled = isEditing
        )
        OutlinedTextField(
            value = state.phoneNumber,
            onValueChange = viewModel::onPhoneNumberChange,
            modifier = Modifier.fillMaxWidth(),
            label = { Text(stringResource(R.string.phone_hint)) },
            enabled = isEditing,
            keyboardOptions = KeyboardOptions.Default.copy(imeAction = ImeAction.Done),
            keyboardActions = KeyboardActions(
                onDone = {
                    if (isEditing) {
                        onSave()
                    }
                }
            )
        )
    }
}

@Composable
private fun KycSection(
    uiState: ProfileViewModel.ProfileUiState,
    onKycVerification: () -> Unit
) {
    val isDark = isSystemInDarkTheme()
    val titleColor = Color.White
    val secondaryText = Color.White
    val verifiedDate = uiState.kycVerifiedAt?.let {
        SimpleDateFormat("dd MMM yyyy", Locale.getDefault()).format(Date(it))
    }
    val lastUpdated = uiState.kycVerifiedAt ?: uiState.kycRejectedAt
    val lastUpdatedText = lastUpdated?.let {
        SimpleDateFormat("dd MMM yyyy", Locale.getDefault()).format(Date(it))
    } ?: stringResource(R.string.placeholder_dash)
    val statusText = when (uiState.kycStatus) {
        KycStatus.PENDING -> stringResource(R.string.kyc_banner_pending)
        KycStatus.VERIFIED -> stringResource(R.string.kyc_badge_verified)
        KycStatus.REJECTED -> stringResource(R.string.kyc_badge_rejected)
    }
    val statusColor = Color.White
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = if (isDark) 10.dp else 4.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF014421)),
        border = premiumCardBorder()
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = stringResource(R.string.kyc_title),
                fontWeight = FontWeight.Bold,
                fontSize = 16.sp,
                color = titleColor
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(text = statusText, color = statusColor, fontWeight = FontWeight.SemiBold)
            Text(
                text = stringResource(R.string.kyc_last_update_format, lastUpdatedText),
                fontSize = 12.sp,
                color = secondaryText
            )
            Spacer(modifier = Modifier.height(12.dp))
            Button(
                onClick = onKycVerification,
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color.White,
                    contentColor = Color(0xFF014421)
                ),
                modifier = premiumButtonModifier(Modifier.fillMaxWidth()),
                border = BorderStroke(2.dp, Color(0xFF014421))
            ) {
                Text(text = stringResource(R.string.kyc_verification_action), color = Color(0xFF014421))
            }
        }
    }
}

@Composable
private fun KycDocumentsSection(
    uiState: ProfileViewModel.ProfileUiState,
    onSubmit: () -> Unit,
    onRetry: () -> Unit,
    pickDocument: (KycDocType) -> Unit
) {
    val isDark = isSystemInDarkTheme()
    val titleColor = Color.White
    val secondaryText = Color.White
    val verifiedDate = uiState.kycVerifiedAt?.let {
        SimpleDateFormat("dd MMM yyyy", Locale.getDefault()).format(Date(it))
    }
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = if (isDark) 10.dp else 4.dp),
        colors = CardDefaults.cardColors(containerColor = Color.Transparent),
        border = premiumCardBorder()
    ) {
        Box(
            modifier = Modifier.fillMaxSize()
        ) {
            Image(
                painter = painterResource(id = R.drawable.card_black_metal_ui),
                contentDescription = null,
                contentScale = ContentScale.Crop,
                modifier = Modifier.fillMaxSize()
            )

            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Text(
                    text = stringResource(R.string.kyc_documents_title),
                    fontWeight = FontWeight.Bold,
                    fontSize = 16.sp,
                    color = titleColor
                )
                when (uiState.kycStatus) {
                    KycStatus.PENDING -> {
                        Banner(
                            text = stringResource(R.string.kyc_banner_text),
                            background = PendingBannerColor,
                            contentColor = Color.White
                        )
                    }
                    KycStatus.VERIFIED -> {
                        StatusBadge(
                            text = stringResource(R.string.kyc_badge_verified),
                            backgroundColor = BerylGreen
                        )
                        verifiedDate?.let {
                            Text(
                                text = stringResource(R.string.kyc_verified_date, it),
                                fontSize = 12.sp,
                                color = secondaryText
                            )
                        }
                    }
                    KycStatus.REJECTED -> {
                        StatusBadge(
                            text = stringResource(R.string.kyc_badge_rejected),
                            backgroundColor = RejectedColor
                        )
                        uiState.kycReason?.let {
                            Text(
                                text = stringResource(R.string.kyc_rejected_reason, it),
                                fontSize = 12.sp,
                                color = Color.White
                            )
                        }
                    }
                }
                KycChecklist(uiState)
                val nextDocument =
                    KycDocType.values().firstOrNull { type ->
                        when (type) {
                            KycDocType.ID -> uiState.kycDocs.idUrl.isNullOrBlank()
                            KycDocType.SELFIE -> uiState.kycDocs.selfieUrl.isNullOrBlank()
                            KycDocType.ADDRESS -> uiState.kycDocs.addressUrl.isNullOrBlank()
                        }
                    }
                Button(
                    onClick = onSubmit,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color(0xFF014421),
                        contentColor = Color.White
                    ),
                    modifier = premiumButtonModifier(),
                    enabled = uiState.kycDocs.completed && uiState.kycStatus != KycStatus.VERIFIED
                ) {
                    Text(text = stringResource(R.string.kyc_submit), color = Color.White)
                }
                if (uiState.kycStatus == KycStatus.REJECTED) {
                    TextButton(onClick = onRetry) {
                        Text(
                            text = stringResource(R.string.kyc_retry),
                            color = Color.White
                        )
                    }
                }
                Spacer(modifier = Modifier.height(16.dp))
                Button(
                    onClick = {
                        nextDocument?.let { pickDocument(it) }
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(52.dp),
                    shape = RoundedCornerShape(12.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color.White,
                        contentColor = Color(0xFF014421)
                    ),
                    border = BorderStroke(2.dp, Color(0xFF014421)),
                    enabled = nextDocument != null
                ) {
                    Text(
                        text = stringResource(R.string.kyc_upload_pieces),
                        color = Color(0xFF014421),
                        fontWeight = FontWeight.Medium
                    )
                }
            }
        }
    }
}

@Composable
private fun Banner(text: String, background: Color, contentColor: Color) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .background(background, RoundedCornerShape(12.dp))
            .padding(12.dp)
    ) {
        Text(text = text, color = contentColor, fontWeight = FontWeight.Medium)
    }
}

@Composable
private fun StatusBadge(text: String, backgroundColor: Color) {
    Surface(
        color = backgroundColor,
        shape = RoundedCornerShape(12.dp)
    ) {
        Text(
            text = text,
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
            color = Color.White,
            fontWeight = FontWeight.Bold,
            fontSize = 12.sp
        )
    }
}

@Composable
private fun KycChecklist(state: ProfileViewModel.ProfileUiState) {
    val isDark = isSystemInDarkTheme()
    val primaryText = Color.White
    val secondaryText = Color.White
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        KycDocType.values().forEach { type ->
            val uploaded = when (type) {
                KycDocType.ID -> state.kycDocs.idUrl?.isNotBlank() == true
                KycDocType.SELFIE -> state.kycDocs.selfieUrl?.isNotBlank() == true
                KycDocType.ADDRESS -> state.kycDocs.addressUrl?.isNotBlank() == true
            }
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                val icon = if (uploaded) Icons.Default.CheckCircle else Icons.Default.RadioButtonUnchecked
                val tint = Color.White
                Icon(icon, contentDescription = null, tint = tint)
                Spacer(modifier = Modifier.width(8.dp))
                Column {
                    Text(
                        text = stringResource(type.labelRes),
                        fontWeight = FontWeight.SemiBold,
                        color = primaryText
                    )
                    if (!uploaded) {
                        Text(
                            text = stringResource(R.string.kyc_upload_pieces),
                            fontSize = 12.sp,
                            color = secondaryText
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun SecuritySection(state: ProfileViewModel.ProfileUiState) {
    val isDark = isSystemInDarkTheme()
    val titleColor = Color.White
    val primaryText = Color.White
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = if (isDark) 10.dp else 4.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF014421)),
        border = premiumCardBorder()
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = stringResource(R.string.profile_section_security),
                fontWeight = FontWeight.Bold,
                fontSize = 16.sp,
                color = titleColor
            )
            Spacer(modifier = Modifier.height(12.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    text = stringResource(R.string.profile_role_label),
                    fontWeight = FontWeight.SemiBold,
                    color = primaryText
                )
                Text(text = state.role.name, fontWeight = FontWeight.Bold, color = primaryText)
            }
            Spacer(modifier = Modifier.height(8.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    text = stringResource(R.string.profile_risk_score),
                    fontWeight = FontWeight.SemiBold,
                    color = primaryText
                )
                Text(
                    text = state.riskScore.toString(),
                    fontWeight = FontWeight.Bold,
                    color = primaryText
                )
            }
        }
    }
}

@Composable
private fun ActionButtonsSection(
    onEditProfile: () -> Unit,
    onSettings: () -> Unit,
    onSignOut: () -> Unit
) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Button(
                onClick = onEditProfile,
                modifier = premiumButtonModifier(Modifier.weight(1f)),
                colors = premiumButtonColors()
            ) {
                Text(text = stringResource(R.string.action_edit_profile), color = MaterialTheme.colorScheme.onPrimary)
            }
        }
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Button(
                onClick = onSettings,
                modifier = premiumButtonModifier(Modifier.weight(1f)),
                colors = premiumButtonColors()
            ) {
                Text(text = stringResource(R.string.action_settings), color = MaterialTheme.colorScheme.onPrimary)
            }
            Button(
                onClick = onSignOut,
                modifier = premiumButtonModifier(Modifier.weight(1f)),
                colors = premiumButtonColors()
            ) {
                Text(text = stringResource(R.string.action_logout), color = MaterialTheme.colorScheme.onPrimary)
            }
        }
    }
}
