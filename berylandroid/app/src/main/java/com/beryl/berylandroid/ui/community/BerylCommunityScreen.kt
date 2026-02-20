package com.beryl.berylandroid.ui.community

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavHostController
import androidx.navigation.NavOptionsBuilder
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.beryl.berylandroid.model.community.MessageType
import com.beryl.berylandroid.ui.community.chat.AttachmentScreen
import com.beryl.berylandroid.ui.community.chat.BerylChatHomeScreen
import com.beryl.berylandroid.ui.community.chat.CallScreen
import com.beryl.berylandroid.ui.community.chat.CameraScreen
import com.beryl.berylandroid.ui.community.chat.ChatDetailScreen
import com.beryl.berylandroid.ui.community.chat.NewChatScreen
import com.beryl.berylandroid.ui.community.chat.SmartHubScreen
import com.beryl.berylandroid.settings.SettingsScreen
import com.beryl.berylandroid.viewmodel.community.CommunityViewModel

@Composable
fun BerylCommunityScreen(
    viewModel: CommunityViewModel = viewModel()
) {
    val communityNavController = rememberNavController()
    CommunityNavHost(
        navController = communityNavController,
        viewModel = viewModel
    )
}

@Composable
internal fun CommunityNavHost(
    navController: NavHostController,
    viewModel: CommunityViewModel
) {
    NavHost(
        navController = navController,
        startDestination = CommunityDestination.ChatHome.route,
        modifier = Modifier.fillMaxSize()
    ) {
        composable(route = CommunityDestination.ChatHome.route) {
            BerylChatHomeScreen(navController = navController, viewModel = viewModel)
        }

        composable(route = CommunityDestination.SmartHub.route) {
            SmartHubScreen(navController = navController, viewModel = viewModel)
        }

        composable(route = CommunityDestination.NewChat.route) {
            NewChatScreen(navController = navController, viewModel = viewModel)
        }

        composable(
            route = CommunityDestination.ChatDetail.route,
            arguments = listOf(
                navArgument(CommunityDestination.ChatDetail.arg) {
                    type = NavType.StringType
                }
            )
        ) { entry ->
            val conversationId = entry.arguments?.getString(CommunityDestination.ChatDetail.arg)
                ?: return@composable
            ChatDetailScreen(
                conversationId = conversationId,
                navController = navController,
                viewModel = viewModel
            )
        }

        composable(
            route = CommunityDestination.Call.route,
            arguments = listOf(
                navArgument(CommunityDestination.Call.conversationArg) {
                    type = NavType.StringType
                },
                navArgument(CommunityDestination.Call.callTypeArg) {
                    type = NavType.StringType
                }
            )
        ) { entry ->
            val conversationId =
                entry.arguments?.getString(CommunityDestination.Call.conversationArg) ?: return@composable
            val callTypeName =
                entry.arguments?.getString(CommunityDestination.Call.callTypeArg)
            val callType = MessageType.values()
                .firstOrNull { it.name == callTypeName } ?: MessageType.CALL_AUDIO

            CallScreen(
                conversationId = conversationId,
                callType = callType,
                navController = navController,
                viewModel = viewModel
            )
        }

        composable(
            route = CommunityDestination.Camera.route,
            arguments = listOf(
                navArgument(CommunityDestination.Camera.arg) {
                    type = NavType.StringType
                }
            )
        ) { entry ->
            val conversationId = entry.arguments?.getString(CommunityDestination.Camera.arg)
                ?: return@composable
            CameraScreen(
                conversationId = conversationId,
                navController = navController,
                viewModel = viewModel
            )
        }

        composable(
            route = CommunityDestination.Attachment.route,
            arguments = listOf(
                navArgument(CommunityDestination.Attachment.arg) {
                    type = NavType.StringType
                }
            )
        ) { entry ->
            val conversationId = entry.arguments?.getString(CommunityDestination.Attachment.arg)
                ?: return@composable
            AttachmentScreen(
                conversationId = conversationId,
                navController = navController,
                viewModel = viewModel
            )
        }

        composable(route = CommunityDestination.Settings.route) {
            SettingsScreen(onBack = { navController.popBackStack() })
        }
    }
}

internal sealed class CommunityDestination(val route: String) {
    object ChatHome : CommunityDestination("chat_home")
    object SmartHub : CommunityDestination("smart_hub")
    object NewChat : CommunityDestination("new_chat")
    object ChatDetail : CommunityDestination("chat_detail/{conversationId}") {
        const val arg = "conversationId"
        fun createRoute(conversationId: String) = "chat_detail/$conversationId"
    }

    object Call : CommunityDestination("call/{conversationId}/{callType}") {
        const val conversationArg = "conversationId"
        const val callTypeArg = "callType"
        fun createRoute(conversationId: String, callType: MessageType) =
            "call/$conversationId/${callType.name}"
    }

    object Camera : CommunityDestination("camera/{conversationId}") {
        const val arg = "conversationId"
        fun createRoute(conversationId: String) = "camera/$conversationId"
    }

    object Attachment : CommunityDestination("attachment/{conversationId}") {
        const val arg = "conversationId"
        fun createRoute(conversationId: String) = "attachment/$conversationId"
    }

    object Settings : CommunityDestination("settings")
}

internal fun NavHostController.safeNavigate(
    route: String,
    builder: NavOptionsBuilder.() -> Unit = {}
) {
    val currentRoute = currentDestination?.route
    if (currentRoute == route) return
    navigate(route, builder)
}
