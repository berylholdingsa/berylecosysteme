package com.beryl.berylandroid.screens

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.ArrowForward
import androidx.compose.material.icons.filled.Chat
import androidx.compose.material.icons.filled.CreditCard
import androidx.compose.material.icons.filled.Eco
import androidx.compose.material.icons.filled.DirectionsCar
import androidx.compose.material.icons.filled.Person
import androidx.compose.material3.IconButton
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.Surface
import androidx.compose.material3.Icon
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.lifecycle.viewmodel.compose.viewModel
import com.beryl.berylandroid.screens.EditProfileScreen
import com.beryl.berylandroid.screens.KycScreen
import com.beryl.berylandroid.screens.MobilityScreen
import com.beryl.berylandroid.screens.PayScreen
import com.beryl.berylandroid.screens.ProfileScreen
import com.beryl.berylandroid.settings.SettingsScreen
import com.beryl.berylandroid.ui.common.BerylWallpaperBackground
import com.beryl.berylandroid.ui.community.BerylCommunityScreen as CommunityChatScreen
import com.beryl.berylandroid.navigation.AppRoutes
import com.beryl.berylandroid.ui.theme.BerylDarkSurfaceStrong
import com.beryl.berylandroid.ui.theme.BerylGreen
import com.beryl.sentinel.sdk.SentinelClient
import com.beryl.esg.ui.navigation.ESGNavGraph
import androidx.compose.ui.res.stringResource
import com.beryl.berylandroid.R
import com.beryl.berylandroid.viewmodel.berylpay.TransferViewModel

@Composable
fun BerylCommunityScreen(
    sentinelClient: SentinelClient,
    onSignOut: () -> Unit
) {
    val communityNavController = rememberNavController()
    val isDark = isSystemInDarkTheme()
    val textColor = if (isDark) Color.White else Color.Unspecified
    val items = remember {
        listOf(
            CommunityTabItem(route = AppRoutes.Community.DISCUSSION, labelRes = R.string.nav_berylcommunity, icon = Icons.Filled.Chat),
            CommunityTabItem(route = AppRoutes.Community.MOBILITY, labelRes = R.string.nav_beryl_emobility, icon = Icons.Filled.DirectionsCar),
            CommunityTabItem(route = AppRoutes.Community.PAY, labelRes = R.string.nav_berylpay, icon = Icons.Filled.CreditCard),
            CommunityTabItem(route = AppRoutes.Community.ESG, labelRes = R.string.nav_beryl_podometresg, icon = Icons.Filled.Eco),
            CommunityTabItem(route = AppRoutes.Community.PROFILE, labelRes = R.string.nav_beryl_utilisateur, icon = Icons.Filled.Person)
        )
    }

    val currentDestination by communityNavController.currentBackStackEntryAsState()
    val currentRoute = currentDestination?.destination?.route

    BerylWallpaperBackground {
        Scaffold(
            containerColor = Color.Transparent,
            bottomBar = {
                NavigationBar(containerColor = if (isDark) BerylDarkSurfaceStrong else BerylGreen) {
                    items.forEach { tab ->
                        NavigationBarItem(
                            selected = currentRoute == tab.route,
                            onClick = {
                                if (currentRoute != tab.route) {
                                    communityNavController.navigate(tab.route) {
                                        popUpTo(communityNavController.graph.startDestinationId) {
                                            saveState = true
                                        }
                                        launchSingleTop = true
                                        restoreState = true
                                    }
                                }
                            },
                            icon = { Icon(imageVector = tab.icon, contentDescription = stringResource(tab.labelRes)) },
                            label = {
                                Text(
                                    stringResource(tab.labelRes),
                                    fontSize = 10.sp,
                                    color = textColor
                                )
                            },
                            colors = NavigationBarItemDefaults.colors(
                                selectedIconColor = Color.White,
                                unselectedIconColor = Color.White,
                                indicatorColor = if (isDark) BerylGreen else Color.White.copy(alpha = 0.15f),
                                selectedTextColor = Color.White,
                                unselectedTextColor = Color.White
                            )
                        )
                    }
                }
            }
        ) { innerPadding ->
            Surface(modifier = Modifier.padding(innerPadding), color = Color.Transparent) {
                val currentIndex = items.indexOfFirst { it.route == currentRoute }.coerceAtLeast(0)
                val backRoute = items.getOrNull(currentIndex - 1)?.route
                val nextRoute = items.getOrNull(currentIndex + 1)?.route
                val canGoBack = communityNavController.previousBackStackEntry != null

                Column(modifier = Modifier.fillMaxSize()) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 8.dp, vertical = 4.dp),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        IconButton(
                            onClick = { communityNavController.popBackStack() },
                            enabled = canGoBack
                        ) {
                            Icon(
                                imageVector = Icons.Filled.ArrowBack,
                                contentDescription = stringResource(R.string.action_back),
                                tint = if (!canGoBack) {
                                    if (isDark) Color.White else BerylGreen.copy(alpha = 0.35f)
                                } else {
                                    if (isDark) Color.White else BerylGreen
                                }
                            )
                        }
                        IconButton(
                            onClick = {
                                nextRoute?.let {
                                    communityNavController.navigate(it) {
                                        popUpTo(communityNavController.graph.startDestinationId) {
                                            saveState = true
                                        }
                                        launchSingleTop = true
                                        restoreState = true
                                    }
                                }
                            },
                            enabled = nextRoute != null
                        ) {
                            Icon(
                                imageVector = Icons.Filled.ArrowForward,
                                contentDescription = stringResource(R.string.action_next),
                                tint = if (nextRoute == null) {
                                    if (isDark) Color.White else BerylGreen.copy(alpha = 0.35f)
                                } else {
                                    if (isDark) Color.White else BerylGreen
                                }
                            )
                        }
                    }
                    NavHost(
                        navController = communityNavController,
                        startDestination = AppRoutes.Community.DISCUSSION,
                        modifier = Modifier.weight(1f)
                    ) {
                        composable(AppRoutes.Community.DISCUSSION) {
                            CommunityChatScreen()
                        }
                        composable(AppRoutes.Community.MOBILITY) {
                            MobilityScreen()
                        }
                        composable(AppRoutes.Community.PAY) {
                            val transferCompleted by it.savedStateHandle
                                .getStateFlow("transfer_done", false)
                                .collectAsState()
                            PayScreen(
                                onNavigateToLogin = onSignOut,
                                onNavigateToTransfer = {
                                    communityNavController.navigate(AppRoutes.Community.TRANSFER)
                                },
                                onNavigateToHistory = {
                                    communityNavController.navigate(AppRoutes.Community.HISTORY)
                                },
                                transferCompleted = transferCompleted,
                                onTransferRefreshConsumed = {
                                    it.savedStateHandle["transfer_done"] = false
                                }
                            )
                        }
                        composable(AppRoutes.Community.HISTORY) {
                            HistoryScreen()
                        }
                        composable(AppRoutes.Community.TRANSFER) {
                            TransferScreen(
                                onContinueToConfirm = {
                                    communityNavController.navigate(AppRoutes.Community.TRANSFER_CONFIRM)
                                }
                            )
                        }
                        composable(AppRoutes.Community.TRANSFER_CONFIRM) {
                            val transferEntry = remember(communityNavController) {
                                communityNavController.getBackStackEntry(AppRoutes.Community.TRANSFER)
                            }
                            val transferViewModel: TransferViewModel = viewModel(transferEntry)
                            ConfirmTransferScreen(
                                viewModel = transferViewModel,
                                onBack = { communityNavController.popBackStack() },
                                onTransferCompleted = {
                                    communityNavController
                                        .getBackStackEntry(AppRoutes.Community.PAY)
                                        .savedStateHandle["transfer_done"] = true
                                    communityNavController.popBackStack(
                                        route = AppRoutes.Community.PAY,
                                        inclusive = false
                                    )
                                }
                            )
                        }
                        composable(AppRoutes.Community.ESG) {
                            ESGNavGraph()
                        }
                        composable(AppRoutes.Community.PROFILE) {
                            ProfileScreen(
                                navController = communityNavController,
                                onSignOut = onSignOut
                            )
                        }
                        composable(AppRoutes.Community.EDIT_PROFILE) {
                            EditProfileScreen(onBack = { communityNavController.popBackStack() })
                        }
                        composable(AppRoutes.Community.KYC) {
                            KycScreen(onBack = { communityNavController.popBackStack() })
                        }
                        composable(AppRoutes.Community.SETTINGS) {
                            SettingsScreen(onBack = { communityNavController.popBackStack() })
                        }
                    }
                }
            }
        }
    }
}

private data class CommunityTabItem(
    val route: String,
    val labelRes: Int,
    val icon: ImageVector
)
