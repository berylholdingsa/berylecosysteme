package com.beryl.berylandroid.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import com.beryl.berylandroid.LoginScreen
import com.beryl.berylandroid.SignupScreen
import com.beryl.berylandroid.screens.HomeScreen
import com.beryl.berylandroid.settings.SettingsScreen
import com.beryl.esg.ui.navigation.ESGNavGraph
import com.beryl.sentinel.sdk.SentinelClient

object AppRoutes {
    const val AUTH = "auth"
    const val SIGNUP = "signup"
    const val HOME = "home/{displayName}"
    const val HOME_BASE = "home"
    const val SETTINGS = "settings"

    object Community {
        const val DISCUSSION = "discussion"
        const val MOBILITY = "mobilite"
        const val PAY = "pay"
        const val HISTORY = "history"
        const val TRANSFER = "transfer"
        const val TRANSFER_CONFIRM = "transfer_confirm"
        const val ESG = "esg"
        const val PROFILE = "profile"
        const val EDIT_PROFILE = "edit_profile"
        const val KYC = "kyc"
        const val SETTINGS = "settings"
        const val BERYL_UTILISATEUR = "beryl_utilisateur"
        const val PROFILE_EDIT = "profile/edit"
        const val PROFILE_KYC = "profile/kyc"
        const val PROFILE_SETTINGS = "profile/settings"
    }

    object Mobility {
        const val RESERVE = "mobility/reserve"
        const val ENERGY = "mobility/energy"
        const val PAY_MY = "mobility/pay_my"
        const val PAY_OTHER = "mobility/pay_other"
        const val LIVE = "mobility/live"
    }
}

@Composable
fun BerylAppNavGraph(
    navController: NavHostController,
    errorMessage: String?,
    sentinelClient: SentinelClient,
    startGoogleSignIn: () -> Unit,
    onNavigateToSignup: () -> Unit,
    onLoginWithEmail: (String, String) -> Unit,
    onLoginWithPhone: (String, String) -> Unit,
    onAppleSignIn: () -> Unit,
    onSignupWithEmail: (String, String, String?) -> Unit,
    onSignOut: () -> Unit
) {
    NavHost(navController = navController, startDestination = AppRoutes.AUTH) {
        composable(AppRoutes.AUTH) {
            LoginScreen(
                errorMessage = errorMessage,
                onGoogleSignIn = startGoogleSignIn,
                onNavigateToSignup = onNavigateToSignup,
                onLoginWithEmail = onLoginWithEmail,
                onLoginWithPhone = onLoginWithPhone,
                onAppleSignIn = onAppleSignIn
            )
        }
        composable(AppRoutes.SIGNUP) {
            SignupScreen(
                errorMessage = errorMessage,
                onBack = { navController.popBackStack() },
                onSignupWithEmail = onSignupWithEmail
            )
        }
        composable(AppRoutes.HOME) {
            HomeScreen(sentinelClient = sentinelClient, onSignOut = onSignOut)
        }
        composable(AppRoutes.SETTINGS) {
            SettingsScreen(onBack = { navController.popBackStack() })
        }
        composable(AppRoutes.Community.ESG) {
            ESGNavGraph()
        }
    }
}
