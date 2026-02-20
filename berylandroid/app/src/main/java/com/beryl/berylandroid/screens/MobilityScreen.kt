package com.beryl.berylandroid.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.beryl.berylandroid.navigation.AppRoutes
import com.beryl.berylandroid.screens.mobility.BerylFontFamily
import com.beryl.berylandroid.screens.mobility.BerylMap
import com.beryl.berylandroid.screens.mobility.EnergyAwareRideScreen
import com.beryl.berylandroid.screens.mobility.LiveRideTrackingScreen
import com.beryl.berylandroid.screens.mobility.PayForOtherScreen
import com.beryl.berylandroid.screens.mobility.PayMyRideScreen
import com.beryl.berylandroid.screens.mobility.ReserveRideScreen
import com.beryl.berylandroid.ui.theme.BerylGreen
import com.beryl.berylandroid.viewmodel.mobility.MobilityViewModel
import com.beryl.berylandroid.R

@Composable
fun MobilityScreen() {
    val navController = rememberNavController()
    val viewModel: MobilityViewModel = viewModel()
    val backStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = backStackEntry?.destination?.route

    val tabs = remember {
        listOf(
            MobilityTab(R.string.mobility_tab_reserve, AppRoutes.Mobility.RESERVE),
            MobilityTab(R.string.mobility_tab_energy, AppRoutes.Mobility.ENERGY),
            MobilityTab(R.string.mobility_tab_pay, AppRoutes.Mobility.PAY_MY),
            MobilityTab(R.string.mobility_tab_fund, AppRoutes.Mobility.PAY_OTHER),
            MobilityTab(R.string.mobility_tab_tracking, AppRoutes.Mobility.LIVE)
        )
    }

    Box(modifier = Modifier.fillMaxSize()) {
        BerylMap(modifier = Modifier.fillMaxSize())

        Column(
            modifier = Modifier
                .fillMaxWidth()
                .align(Alignment.TopCenter)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp, vertical = 16.dp),
            verticalArrangement = Arrangement.spacedBy(18.dp)
        ) {
            Text(
                text = stringResource(R.string.mobility_title),
                fontFamily = BerylFontFamily,
                fontSize = 18.sp,
                color = Color.Black
            )
            Spacer(modifier = Modifier.height(8.dp))
            LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                items(tabs.size) { index ->
                    val tab = tabs[index]
                    val selected = currentRoute == tab.route
                    Row(
                        modifier = Modifier
                            .background(
                                color = if (selected) BerylGreen else Color(0xFFF1F4F2),
                                shape = RoundedCornerShape(50)
                            )
                            .clickable {
                                if (!selected) {
                                    navController.navigate(tab.route) {
                                        popUpTo(navController.graph.startDestinationId) {
                                            saveState = true
                                        }
                                        launchSingleTop = true
                                        restoreState = true
                                    }
                                }
                            }
                            .padding(horizontal = 14.dp, vertical = 6.dp)
                            .height(28.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = stringResource(tab.labelRes),
                            fontFamily = BerylFontFamily,
                            fontSize = 12.sp,
                            color = if (selected) Color.White else Color.Black
                        )
                    }
                }
            }
            Spacer(modifier = Modifier.height(6.dp))
            Text(
                text = stringResource(R.string.mobility_tagline),
                fontFamily = BerylFontFamily,
                fontSize = 11.sp,
                color = Color.Black.copy(alpha = 0.5f)
            )

            NavHost(
                navController = navController,
                startDestination = AppRoutes.Mobility.RESERVE,
                modifier = Modifier.fillMaxWidth()
            ) {
                composable(AppRoutes.Mobility.RESERVE) {
                    ReserveRideScreen(
                        viewModel = viewModel,
                        onRequestRide = {
                            navController.navigate(AppRoutes.Mobility.LIVE) {
                                popUpTo(navController.graph.startDestinationId) {
                                    saveState = true
                                }
                                launchSingleTop = true
                                restoreState = true
                            }
                        }
                    )
                }
                composable(AppRoutes.Mobility.ENERGY) {
                    EnergyAwareRideScreen(viewModel = viewModel)
                }
                composable(AppRoutes.Mobility.PAY_MY) {
                    PayMyRideScreen(viewModel = viewModel)
                }
                composable(AppRoutes.Mobility.PAY_OTHER) {
                    PayForOtherScreen(viewModel = viewModel)
                }
                composable(AppRoutes.Mobility.LIVE) {
                    LiveRideTrackingScreen(viewModel = viewModel)
                }
            }
        }
    }
}

private data class MobilityTab(
    val labelRes: Int,
    val route: String
)
