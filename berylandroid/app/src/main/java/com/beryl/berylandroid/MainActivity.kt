package com.beryl.berylandroid

import android.app.Activity
import android.content.Context
import android.net.Uri
import android.os.Bundle
import com.beryl.berylandroid.util.ProfileValidation
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Image
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.layout.onSizeChanged
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.googlefonts.Font
import androidx.compose.ui.text.googlefonts.GoogleFont
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.compose.rememberNavController
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.viewmodel.compose.viewModel
import com.google.android.gms.auth.api.signin.GoogleSignIn
import com.google.android.gms.auth.api.signin.GoogleSignInClient
import com.google.android.gms.auth.api.signin.GoogleSignInOptions
import com.google.android.gms.common.api.ApiException
import com.beryl.berylandroid.model.auth.UserSettings
import com.beryl.berylandroid.navigation.AppRoutes
import com.beryl.berylandroid.navigation.BerylAppNavGraph
import com.beryl.berylandroid.settings.LanguageOption
import com.beryl.berylandroid.settings.LocaleHelper
import com.beryl.berylandroid.settings.ProvideAppLocale
import com.beryl.berylandroid.settings.SettingsRepository
import com.beryl.berylandroid.settings.SettingsViewModel
import com.beryl.berylandroid.settings.SettingsViewModelFactory
import com.beryl.berylandroid.settings.ThemeOption
import com.beryl.berylandroid.ui.common.BerylWallpaperBackground
import com.beryl.berylandroid.ui.theme.BerylAndroidTheme
import com.beryl.berylandroid.ui.theme.BerylGreen
import com.beryl.berylandroid.ui.theme.premiumButtonColors
import com.beryl.berylandroid.ui.theme.premiumButtonModifier
import com.beryl.berylandroid.ui.theme.premiumCardBorder
import com.beryl.berylandroid.ui.theme.premiumCardColors
import com.beryl.berylandroid.viewmodel.auth.AuthViewModel
import com.beryl.sentinel.sdk.SentinelClient
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlin.math.roundToInt

private const val AUTH_SLOGAN_TEXT = "Batir aujourd'hui la Vision Africaine de Demain"
private val BerylPremiumFont = FontFamily(
    Font(
        googleFont = GoogleFont("Playfair Display"),
        fontProvider = GoogleFont.Provider(
            providerAuthority = "com.google.android.gms.fonts",
            providerPackage = "com.google.android.gms",
            certificates = R.array.com_google_android_gms_fonts_certs
        ),
        weight = FontWeight.Bold
    )
)
private val AuthButtonGreen = Color(0xFF014421)

class MainActivity : ComponentActivity() {
    private lateinit var googleSignInClient: GoogleSignInClient
    private var currentLanguageTag: String = LanguageOption.FRENCH.tag
    private val settingsRepository by lazy { SettingsRepository(applicationContext) }

    override fun attachBaseContext(newBase: Context) {
        val repository = SettingsRepository(newBase.applicationContext)
        val initialTag = runBlocking {
            repository.settingsFlow
                .map { it.language.tag }
                .first()
        }
        currentLanguageTag = initialTag
        val localizedContext = LocaleHelper.wrapContextWithLocale(newBase, initialTag)
        super.attachBaseContext(localizedContext)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val gso = GoogleSignInOptions.Builder(GoogleSignInOptions.DEFAULT_SIGN_IN)
            .requestIdToken(getString(R.string.default_web_client_id))
            .requestEmail()
            .build()

        googleSignInClient = GoogleSignIn.getClient(this, gso)

        observeLanguageChanges()

        setContent {
            val authViewModel: AuthViewModel = viewModel()
            BerylApp(googleSignInClient = googleSignInClient, authViewModel = authViewModel)
        }
    }

    private fun observeLanguageChanges() {
        lifecycleScope.launch {
            settingsRepository.settingsFlow
                .map { it.language.tag }
                .distinctUntilChanged()
                .collect { tag ->
                    if (tag != currentLanguageTag) {
                        currentLanguageTag = tag
                        LocaleHelper.applyLocale(this@MainActivity, tag)
                        recreate()
                    }
                }
        }
    }
}

@Composable
fun BerylApp(
    googleSignInClient: GoogleSignInClient,
    authViewModel: AuthViewModel
) {
    val navController = rememberNavController()
    val context = LocalContext.current
    val activity = context as? Activity
    val settingsViewModel: SettingsViewModel = viewModel(
        factory = SettingsViewModelFactory(context)
    )
    val settings by settingsViewModel.settings.collectAsState()
    val appName = stringResource(R.string.app_name)
    val sentinelClient = remember {
        SentinelClient(
            context = context,
            baseUrl = if (BuildConfig.DEBUG) BuildConfig.BASE_URL_DEBUG else BuildConfig.BASE_URL_PROD,
            apiKey = BuildConfig.SENTINEL_API_KEY, // TODO: Set via gradle properties or CI env.
            apiSecret = BuildConfig.SENTINEL_API_SECRET // TODO: Set via gradle properties or CI env.
        )
    }
    val authState by authViewModel.authState.collectAsState()
    val errorMessage by authViewModel.errorMessage.collectAsState()
    val errorGoogleToken = stringResource(R.string.auth_error_google_token)
    val errorGoogleFailed = stringResource(R.string.auth_error_google_failed)
    val errorGoogleCancelled = stringResource(R.string.auth_error_google_cancelled)
    val errorAppleStart = stringResource(R.string.auth_error_apple_start)
    val errorPhoneStart = stringResource(R.string.auth_error_phone_start)

    val googleSignInLauncher =
        rememberLauncherForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
            if (result.resultCode == Activity.RESULT_OK) {
                val task = GoogleSignIn.getSignedInAccountFromIntent(result.data)
                try {
                    val account = task.getResult(ApiException::class.java)
                    val idToken = account?.idToken
                    if (idToken != null) {
                        authViewModel.signInWithGoogle(idToken)
                    } else {
                        authViewModel.reportError(errorGoogleToken)
                    }
                } catch (e: ApiException) {
                    authViewModel.reportError(e.localizedMessage ?: errorGoogleFailed)
                }
            } else {
                authViewModel.reportError(errorGoogleCancelled)
            }
        }

    val startGoogleSignIn = {
        googleSignInClient.signOut()
        googleSignInLauncher.launch(googleSignInClient.signInIntent)
    }

    val startAppleSignIn = {
        val hostActivity = activity
        if (hostActivity != null) {
            authViewModel.signInWithApple(hostActivity)
        } else {
            authViewModel.reportError(errorAppleStart)
        }
    }

    val startPhoneSignIn: (String, String) -> Unit = { phoneNumber, smsCode ->
        val hostActivity = activity
        if (hostActivity != null) {
            authViewModel.signInWithPhone(hostActivity, phoneNumber, smsCode)
        } else {
            authViewModel.reportError(errorPhoneStart)
        }
    }
    LaunchedEffect(authState) {
        val destination = navController.currentDestination
        when (authState) {
            is AuthViewModel.AuthState.Authenticated -> {
                val user = (authState as AuthViewModel.AuthState.Authenticated).user
                val name = user.displayName ?: user.email ?: appName
                val homeRoute = "${AppRoutes.HOME_BASE}/${Uri.encode(name)}"
                if (destination?.route?.startsWith("${AppRoutes.HOME_BASE}/") != true) {
                    navController.navigate(homeRoute) {
                        popUpTo(AppRoutes.AUTH) { inclusive = true }
                        launchSingleTop = true
                    }
                }
            }
            is AuthViewModel.AuthState.Unauthenticated -> {
                navController.navigate(AppRoutes.AUTH) {
                    popUpTo(navController.graph.id) { inclusive = true }
                    launchSingleTop = true
                }
            }
            else -> Unit
        }
    }

    val darkTheme = when (settings.theme) {
        ThemeOption.SYSTEM -> isSystemInDarkTheme()
        ThemeOption.DARK -> true
        ThemeOption.LIGHT -> false
    }

    ProvideAppLocale(settings.language.tag) {
        BerylAndroidTheme(darkTheme = darkTheme, dynamicColor = false) {
            Surface(modifier = Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
                when (authState) {
                    is AuthViewModel.AuthState.Loading -> {
                        Box(
                            modifier = Modifier.fillMaxSize(),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(stringResource(R.string.app_loading), color = MaterialTheme.colorScheme.onBackground)
                        }
                    }
                    else -> {
                        BerylAppNavGraph(
                            navController = navController,
                            errorMessage = errorMessage,
                            sentinelClient = sentinelClient,
                            startGoogleSignIn = startGoogleSignIn,
                            onNavigateToSignup = { navController.navigate(AppRoutes.SIGNUP) },
                            onLoginWithEmail = authViewModel::signInWithEmail,
                            onLoginWithPhone = startPhoneSignIn,
                            onAppleSignIn = startAppleSignIn,
                            onSignupWithEmail = { email, password, displayName ->
                                authViewModel.registerWithEmail(email, password, displayName)
                            },
                            onSignOut = authViewModel::signOut
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun LoginScreen(
    errorMessage: String?,
    onGoogleSignIn: () -> Unit,
    onNavigateToSignup: () -> Unit,
    onLoginWithEmail: (String, String) -> Unit,
    onLoginWithPhone: (String, String) -> Unit,
    onAppleSignIn: () -> Unit
) {
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var passwordVisible by remember { mutableStateOf(false) }
    var emailError by remember { mutableStateOf(false) }
    var passwordError by remember { mutableStateOf(false) }
    var lastAttemptWasPhone by remember { mutableStateOf(false) }
    val isDark = isSystemInDarkTheme()
    val titleColor = MaterialTheme.colorScheme.onBackground
    val mutedTitle = MaterialTheme.colorScheme.onBackground.copy(alpha = 0.75f)
    val authFieldColors = OutlinedTextFieldDefaults.colors(
        focusedTextColor = Color.White,
        unfocusedTextColor = Color.White,
        cursorColor = Color.White,
        focusedPlaceholderColor = Color.White.copy(alpha = 0.6f),
        unfocusedPlaceholderColor = Color.White.copy(alpha = 0.6f),
        focusedLabelColor = Color.White,
        unfocusedLabelColor = Color.White
    )

    BerylWallpaperBackground {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 24.dp, vertical = 16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
        Spacer(modifier = Modifier.height(12.dp))
        Image(
            painter = painterResource(id = R.drawable.logo),
            contentDescription = stringResource(R.string.brand_logo_content_description),
            modifier = Modifier.size(170.dp)
        )
        Text(
            text = stringResource(R.string.app_name),
            style = TextStyle(
                fontFamily = BerylPremiumFont,
                fontWeight = FontWeight.Bold,
                fontSize = 32.sp,
                letterSpacing = 1.5.sp,
                color = titleColor
            ),
            modifier = Modifier.padding(top = 12.dp, bottom = 4.dp)
        )
        ScrollingAuthSlogan(
            color = mutedTitle,
            modifier = Modifier.padding(bottom = 24.dp)
        )

        val cardBorder = if (isDark) premiumCardBorder() else BorderStroke(1.dp, BerylGreen.copy(alpha = 0.2f))
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(18.dp),
            elevation = CardDefaults.cardElevation(defaultElevation = if (isDark) 12.dp else 8.dp),
            border = cardBorder,
            colors = CardDefaults.cardColors(containerColor = Color.Transparent)
        ) {
            Box {
                Image(
                    painter = painterResource(id = R.drawable.card_berylpay_green_metal),
                    contentDescription = null,
                    modifier = Modifier.matchParentSize(),
                    contentScale = ContentScale.Crop
                )
                Column(modifier = Modifier.padding(20.dp)) {
                val performLogin = {
                    val trimmedInput = email.trim()
                    val looksLikePhone = trimmedInput.isNotEmpty() &&
                        !trimmedInput.contains("@") &&
                        trimmedInput.any { it.isDigit() }
                    val isPhone = isPhoneNumber(trimmedInput)
                    lastAttemptWasPhone = looksLikePhone
                    if (isPhone) {
                        emailError = false
                        if (password.isBlank()) {
                            passwordError = false
                            onLoginWithPhone(trimmedInput, "")
                        } else if (password.length < 6) {
                            passwordError = true
                        } else {
                            passwordError = false
                            onLoginWithPhone(trimmedInput, password)
                        }
                    } else {
                        val validEmail = ProfileValidation.isEmailValid(trimmedInput)
                        val validPassword = password.length >= 6
                        emailError = !validEmail
                        passwordError = !validPassword
                        if (validEmail && validPassword) {
                            onLoginWithEmail(trimmedInput, password)
                        }
                    }
                }
                OutlinedTextField(
                    value = email,
                    onValueChange = {
                        email = it
                        emailError = false
                    },
                    placeholder = { Text(stringResource(R.string.login_email_or_phone_placeholder)) },
                    keyboardOptions = KeyboardOptions.Default.copy(keyboardType = KeyboardType.Email),
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(18.dp),
                    colors = authFieldColors
                )
                if (emailError) {
                    Text(
                        text = if (lastAttemptWasPhone) {
                            stringResource(R.string.login_invalid_phone)
                        } else {
                            stringResource(R.string.login_invalid_email)
                        },
                        color = Color.Red,
                        fontSize = 12.sp,
                        modifier = Modifier.padding(top = 4.dp)
                    )
                }

                Spacer(modifier = Modifier.height(16.dp))

                OutlinedTextField(
                    value = password,
                    onValueChange = {
                        password = it
                        passwordError = false
                    },
                    placeholder = { Text(stringResource(R.string.password_label)) },
                    visualTransformation =
                        if (passwordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                    trailingIcon = {
                        IconButton(onClick = { passwordVisible = !passwordVisible }) {
                            Icon(
                                imageVector = if (passwordVisible) {
                                    Icons.Default.VisibilityOff
                                } else {
                                    Icons.Default.Visibility
                                },
                                contentDescription = null,
                                tint = Color.White
                            )
                        }
                    },
                    keyboardOptions = KeyboardOptions.Default.copy(imeAction = ImeAction.Done),
                    keyboardActions = KeyboardActions(onDone = { performLogin() }),
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(18.dp),
                    colors = authFieldColors
                )
                if (passwordError) {
                    Text(
                        text = if (lastAttemptWasPhone) {
                            stringResource(R.string.login_password_short_phone_code)
                        } else {
                            stringResource(R.string.login_password_short)
                        },
                        color = Color.Red,
                        fontSize = 12.sp,
                        modifier = Modifier.padding(top = 4.dp)
                    )
                }

                Spacer(modifier = Modifier.height(20.dp))

                val loginButtonInteraction = remember { MutableInteractionSource() }
                val loginButtonPressed by loginButtonInteraction.collectIsPressedAsState()
                Button(
                    onClick = { performLogin() },
                    interactionSource = loginButtonInteraction,
                    modifier = premiumButtonModifier(
                        Modifier
                            .fillMaxWidth()
                            .height(52.dp)
                    ),
                    shape = RoundedCornerShape(18.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (loginButtonPressed) AuthButtonGreen else Color.White,
                        contentColor = if (loginButtonPressed) Color.White else AuthButtonGreen
                    ),
                    border = BorderStroke(2.dp, AuthButtonGreen)
                ) {
                    Text(
                        text = stringResource(R.string.login_cta),
                        color = if (loginButtonPressed) Color.White else AuthButtonGreen,
                        fontWeight = FontWeight.Medium,
                        fontSize = 16.sp
                    )
                }

                Spacer(modifier = Modifier.height(16.dp))

                SocialButton(
                    text = stringResource(R.string.login_google),
                    logoText = stringResource(R.string.login_google_logo),
                    onClick = onGoogleSignIn
                )
                Spacer(modifier = Modifier.height(12.dp))
                val appleButtonInteraction = remember { MutableInteractionSource() }
                val appleButtonPressed by appleButtonInteraction.collectIsPressedAsState()
                Button(
                    onClick = onAppleSignIn,
                    interactionSource = appleButtonInteraction,
                    modifier = premiumButtonModifier(
                        Modifier
                            .fillMaxWidth()
                            .height(48.dp)
                    ),
                    shape = RoundedCornerShape(18.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (appleButtonPressed) AuthButtonGreen else Color.White,
                        contentColor = if (appleButtonPressed) Color.White else AuthButtonGreen
                    ),
                    border = BorderStroke(2.dp, AuthButtonGreen)
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            painter = painterResource(id = R.drawable.ic_apple_logo),
                            contentDescription = "Apple",
                            tint = Color.Black,
                            modifier = Modifier.size(22.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = stringResource(R.string.login_apple),
                            fontSize = 14.sp,
                            fontWeight = FontWeight.Medium,
                            color = if (appleButtonPressed) Color.White else AuthButtonGreen
                        )
                    }
                }
            }
            }
        }

        errorMessage?.let {
            Text(
                text = it,
                color = Color.Red,
                fontSize = 12.sp,
                modifier = Modifier.padding(top = 12.dp)
            )
        }

        Spacer(modifier = Modifier.weight(1f))

        Row(
            horizontalArrangement = Arrangement.Center,
            modifier = Modifier.fillMaxWidth()
        ) {
            Text(
                text = stringResource(R.string.login_no_account),
                color = mutedTitle
            )
            TextButton(onClick = onNavigateToSignup) {
                Text(
                    text = stringResource(R.string.login_create_account),
            color = titleColor,
            fontWeight = FontWeight.Bold
        )
            }
        }

        Spacer(modifier = Modifier.height(12.dp))
        }
    }
}

@Composable
fun SignupScreen(
    errorMessage: String?,
    onBack: () -> Unit,
    onSignupWithEmail: (String, String, String) -> Unit
) {
    var name by remember { mutableStateOf("") }
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var confirmPassword by remember { mutableStateOf("") }
    var showErrors by remember { mutableStateOf(false) }
    val isDark = isSystemInDarkTheme()
    val titleColor = MaterialTheme.colorScheme.onBackground
    val mutedTitle = MaterialTheme.colorScheme.onBackground.copy(alpha = 0.75f)

    val isNameValid = name.isNotBlank()
    val isEmailValid = ProfileValidation.isEmailValid(email)
    val isPasswordValid = password.length >= 6
    val isPasswordsMatch = password == confirmPassword && confirmPassword.isNotBlank()

    val performSignup = {
        showErrors = true
        if (isNameValid && isEmailValid && isPasswordValid && isPasswordsMatch) {
            onSignupWithEmail(name, email, password)
        }
    }

    BerylWallpaperBackground {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 24.dp, vertical = 16.dp)
        ) {
        Spacer(modifier = Modifier.height(8.dp))
        Image(
            painter = painterResource(id = R.drawable.logo),
            contentDescription = stringResource(R.string.brand_logo_content_description),
            modifier = Modifier
                .size(165.dp)
                .align(Alignment.CenterHorizontally)
        )
        Text(
            text = stringResource(R.string.app_name),
            style = TextStyle(
                fontFamily = BerylPremiumFont,
                fontWeight = FontWeight.Bold,
                fontSize = 32.sp,
                letterSpacing = 1.5.sp,
                color = titleColor
            ),
            modifier = Modifier
                .align(Alignment.CenterHorizontally)
                .padding(top = 8.dp)
        )
        ScrollingAuthSlogan(
            color = mutedTitle,
            modifier = Modifier
                .padding(bottom = 24.dp, top = 4.dp)
        )

        val cardBorder = if (isDark) premiumCardBorder() else BorderStroke(1.dp, BerylGreen.copy(alpha = 0.2f))
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(18.dp),
            elevation = CardDefaults.cardElevation(defaultElevation = if (isDark) 12.dp else 6.dp),
            border = cardBorder,
            colors = CardDefaults.cardColors(containerColor = Color.Transparent)
        ) {
            Box {
                Image(
                    painter = painterResource(id = R.drawable.card_berylpay_green_metal),
                    contentDescription = null,
                    modifier = Modifier.matchParentSize(),
                    contentScale = ContentScale.Crop
                )
                Column(modifier = Modifier.padding(20.dp)) {
                RoundedInputField(
                    value = name,
                    onValueChange = { name = it },
                    placeholder = stringResource(R.string.signup_full_name_placeholder)
                )
                if (showErrors && !isNameValid) FieldError(stringResource(R.string.signup_name_required))

                Spacer(modifier = Modifier.height(16.dp))

                RoundedInputField(
                    value = email,
                    onValueChange = { email = it },
                    placeholder = stringResource(R.string.signup_email_placeholder)
                )
                if (showErrors && !isEmailValid) FieldError(stringResource(R.string.signup_email_invalid))

                Spacer(modifier = Modifier.height(16.dp))

                RoundedInputField(
                    value = password,
                    onValueChange = { password = it },
                    placeholder = stringResource(R.string.password_label),
                    isPassword = true
                )
                if (showErrors && !isPasswordValid) FieldError(stringResource(R.string.signup_password_min))

                Spacer(modifier = Modifier.height(16.dp))

                RoundedInputField(
                    value = confirmPassword,
                    onValueChange = { confirmPassword = it },
                    placeholder = stringResource(R.string.signup_confirm_password_placeholder),
                    isPassword = true,
                    imeAction = ImeAction.Done,
                    keyboardActions = KeyboardActions(onDone = { performSignup() })
                )
                if (showErrors && !isPasswordsMatch) FieldError(stringResource(R.string.signup_password_mismatch))
            }
            }
        }

        Spacer(modifier = Modifier.height(24.dp))

        Text(
            text = stringResource(R.string.signup_benefits_title),
            fontSize = 14.sp,
            fontWeight = FontWeight.Medium,
            color = titleColor
        )
        Text(
            text = stringResource(R.string.signup_benefits_list),
            fontSize = 12.sp,
            color = mutedTitle,
            modifier = Modifier.padding(top = 4.dp)
        )

        Spacer(modifier = Modifier.height(24.dp))

        Button(
            onClick = { performSignup() },
            modifier = premiumButtonModifier(
                Modifier
                    .fillMaxWidth()
                    .height(52.dp)
            ),
            shape = RoundedCornerShape(18.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = AuthButtonGreen,
                contentColor = Color.White
            )
        ) {
            Text(
                text = stringResource(R.string.signup_create_account),
                color = Color.White,
                fontWeight = FontWeight.Medium,
                fontSize = 16.sp
            )
        }

        Spacer(modifier = Modifier.height(12.dp))

        errorMessage?.let {
            Text(
                text = it,
                color = Color.Red,
                fontSize = 12.sp,
                modifier = Modifier
                    .align(Alignment.CenterHorizontally)
                    .padding(top = 8.dp)
            )
        }

        Spacer(modifier = Modifier.weight(1f))

        TextButton(onClick = onBack, modifier = Modifier.align(Alignment.CenterHorizontally)) {
            Text(text = stringResource(R.string.signup_back_to_login), color = titleColor, fontWeight = FontWeight.SemiBold)
        }
        Spacer(modifier = Modifier.height(12.dp))
        }
    }
}

@Composable
private fun ScrollingAuthSlogan(
    color: Color,
    modifier: Modifier = Modifier
) {
    var containerWidthPx by remember { mutableIntStateOf(0) }
    var textWidthPx by remember { mutableIntStateOf(0) }

    val infiniteTransition = rememberInfiniteTransition(label = "auth_slogan_scroll")
    val startX = if (containerWidthPx > 0) containerWidthPx.toFloat() else 1000f
    val endX = if (textWidthPx > 0) -textWidthPx.toFloat() else -1000f

    val offsetX by infiniteTransition.animateFloat(
        initialValue = startX,
        targetValue = endX,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 18000, easing = LinearEasing)
        ),
        label = "auth_slogan_offset"
    )

    Box(
        modifier = modifier
            .fillMaxWidth()
            .clipToBounds()
            .onSizeChanged { containerWidthPx = it.width }
    ) {
        Text(
            text = AUTH_SLOGAN_TEXT,
            fontSize = 14.sp,
            color = color,
            maxLines = 1,
            softWrap = false,
            modifier = Modifier
                .wrapContentWidth(unbounded = true)
                .onSizeChanged { textWidthPx = it.width }
                .offset { IntOffset(offsetX.roundToInt(), 0) }
        )
    }
}

@Composable
fun RoundedInputField(
    value: String,
    onValueChange: (String) -> Unit,
    placeholder: String,
    isPassword: Boolean = false,
    imeAction: ImeAction = ImeAction.Default,
    keyboardActions: KeyboardActions = KeyboardActions.Default
) {
    var passwordVisible by remember { mutableStateOf(false) }
    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        placeholder = { Text(placeholder) },
        singleLine = true,
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(18.dp),
        visualTransformation = if (isPassword) {
            if (passwordVisible) VisualTransformation.None else PasswordVisualTransformation()
        } else {
            VisualTransformation.None
        },
        trailingIcon = if (isPassword) {
            {
                IconButton(onClick = { passwordVisible = !passwordVisible }) {
                    Icon(
                        imageVector = if (passwordVisible) {
                            Icons.Default.VisibilityOff
                        } else {
                            Icons.Default.Visibility
                        },
                        contentDescription = null,
                        tint = Color.White
                    )
                }
            }
        } else {
            null
        },
        keyboardOptions = KeyboardOptions.Default.copy(imeAction = imeAction),
        keyboardActions = keyboardActions,
        colors = OutlinedTextFieldDefaults.colors(
            focusedTextColor = Color.White,
            unfocusedTextColor = Color.White,
            cursorColor = Color.White,
            focusedPlaceholderColor = Color.White.copy(alpha = 0.6f),
            unfocusedPlaceholderColor = Color.White.copy(alpha = 0.6f),
            focusedLabelColor = Color.White,
            unfocusedLabelColor = Color.White
        )
    )
}

@Composable
fun FieldError(message: String) {
    Text(
        text = message,
        color = Color.Red,
        fontSize = 12.sp,
        modifier = Modifier.padding(top = 4.dp)
    )
}

@Composable
fun SocialButton(text: String, logoText: String, onClick: () -> Unit) {
    val interactionSource = remember { MutableInteractionSource() }
    val isPressed by interactionSource.collectIsPressedAsState()
    val contentColor = if (isPressed) Color.White else AuthButtonGreen
    Button(
        onClick = onClick,
        interactionSource = interactionSource,
        modifier = premiumButtonModifier(
            Modifier
                .fillMaxWidth()
                .height(48.dp)
        ),
        shape = RoundedCornerShape(18.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = if (isPressed) AuthButtonGreen else Color.White,
            contentColor = contentColor
        ),
        border = BorderStroke(2.dp, AuthButtonGreen)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(
                text = logoText,
                fontSize = 16.sp,
                fontWeight = FontWeight.Bold,
                color = contentColor
            )
            Spacer(modifier = Modifier.width(10.dp))
            Text(text = text, fontSize = 14.sp, fontWeight = FontWeight.Medium, color = contentColor)
        }
    }
}

private fun isPhoneNumber(input: String): Boolean {
    val trimmed = input.trim()
    if (trimmed.isEmpty() || trimmed.contains("@")) {
        return false
    }
    return ProfileValidation.isPhoneValid(trimmed)
}
