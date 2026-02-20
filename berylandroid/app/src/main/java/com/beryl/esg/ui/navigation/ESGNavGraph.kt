package com.beryl.esg.ui.navigation

import android.net.Uri
import androidx.compose.runtime.Composable
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.beryl.esg.ui.screens.ESGConfidenceScreen
import com.beryl.esg.ui.screens.ESGHomeScreen
import com.beryl.esg.ui.screens.ESGImpactDetailScreen
import com.beryl.esg.ui.screens.ESGMethodologyScreen
import com.beryl.esg.ui.screens.ESGMrvReportScreen
import com.beryl.esg.ui.screens.ESGVerificationScreen

object ESGRoutes {
    const val HOME = "esg/home"
    const val IMPACT_DETAIL = "esg/impact/{tripId}"
    const val CONFIDENCE = "esg/confidence/{tripId}"
    const val VERIFICATION = "esg/verification/{tripId}"
    const val MRV_REPORT = "esg/mrv"
    const val METHODOLOGY = "esg/methodology"

    fun impactDetail(tripId: String): String = "esg/impact/${Uri.encode(tripId)}"
    fun confidence(tripId: String): String = "esg/confidence/${Uri.encode(tripId)}"
    fun verification(tripId: String): String = "esg/verification/${Uri.encode(tripId)}"
}

@Composable
fun ESGNavGraph() {
    val navController = rememberNavController()

    NavHost(
        navController = navController,
        startDestination = ESGRoutes.HOME
    ) {
        composable(ESGRoutes.HOME) {
            ESGHomeScreen(
                onOpenImpactDetail = { tripId ->
                    navController.navigate(ESGRoutes.impactDetail(tripId))
                },
                onOpenConfidence = { tripId ->
                    navController.navigate(ESGRoutes.confidence(tripId))
                },
                onOpenVerification = { tripId ->
                    navController.navigate(ESGRoutes.verification(tripId))
                },
                onOpenMrvReport = {
                    navController.navigate(ESGRoutes.MRV_REPORT)
                },
                onOpenMethodology = {
                    navController.navigate(ESGRoutes.METHODOLOGY)
                }
            )
        }

        composable(
            route = ESGRoutes.IMPACT_DETAIL,
            arguments = listOf(navArgument("tripId") { type = NavType.StringType })
        ) { backStackEntry ->
            val tripId = backStackEntry.arguments?.getString("tripId").orEmpty()
            ESGImpactDetailScreen(
                tripId = tripId,
                onBack = { navController.popBackStack() },
                onOpenConfidence = { selectedTripId ->
                    navController.navigate(ESGRoutes.confidence(selectedTripId))
                },
                onOpenVerification = { selectedTripId ->
                    navController.navigate(ESGRoutes.verification(selectedTripId))
                }
            )
        }

        composable(
            route = ESGRoutes.CONFIDENCE,
            arguments = listOf(navArgument("tripId") { type = NavType.StringType })
        ) { backStackEntry ->
            val tripId = backStackEntry.arguments?.getString("tripId").orEmpty()
            ESGConfidenceScreen(
                tripId = tripId,
                onBack = { navController.popBackStack() },
                onOpenVerification = { selectedTripId ->
                    navController.navigate(ESGRoutes.verification(selectedTripId))
                }
            )
        }

        composable(
            route = ESGRoutes.VERIFICATION,
            arguments = listOf(navArgument("tripId") { type = NavType.StringType })
        ) { backStackEntry ->
            val tripId = backStackEntry.arguments?.getString("tripId").orEmpty()
            ESGVerificationScreen(
                tripId = tripId,
                onBack = { navController.popBackStack() }
            )
        }

        composable(ESGRoutes.MRV_REPORT) {
            ESGMrvReportScreen(
                onBack = { navController.popBackStack() },
                onOpenMethodology = {
                    navController.navigate(ESGRoutes.METHODOLOGY)
                }
            )
        }

        composable(ESGRoutes.METHODOLOGY) {
            ESGMethodologyScreen(
                onBack = { navController.popBackStack() }
            )
        }
    }
}
