package com.beryl.berylandroid.screens.mobility

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Bolt
import androidx.compose.material.icons.outlined.Eco
import androidx.compose.material.icons.outlined.EvStation
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.beryl.berylandroid.R
import com.beryl.berylandroid.ui.theme.BerylGreen
import com.beryl.berylandroid.viewmodel.mobility.MobilityViewModel

@Composable
fun EnergyAwareRideScreen(
    viewModel: MobilityViewModel
) {
    val state by viewModel.uiState.collectAsState()
    Box(modifier = Modifier.fillMaxSize()) {
        Box(
            modifier = Modifier
                .matchParentSize()
                .background(
                    Brush.verticalGradient(
                        colors = listOf(Color.Transparent, BerylGreen.copy(alpha = 0.16f))
                    )
                )
        )

        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            BerylSectionCard(modifier = Modifier.fillMaxWidth()) {
                BerylTitle(text = stringResource(R.string.mobility_energy_optimization_title))
                Spacer(modifier = Modifier.height(6.dp))
                BerylSubtitle(text = stringResource(R.string.mobility_energy_optimization_subtitle))
                Spacer(modifier = Modifier.height(12.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    BerylStatChip(label = stringResource(R.string.mobility_battery), value = "${state.batteryPercent}%")
                    BerylStatChip(label = stringResource(R.string.mobility_distance), value = "${state.remainingRangeKm} km")
                    BerylStatChip(label = stringResource(R.string.mobility_stops), value = "${state.energyStops} arrêt")
                }
                Spacer(modifier = Modifier.height(12.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(imageVector = Icons.Outlined.EvStation, contentDescription = null, tint = BerylGreen)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = stringResource(R.string.mobility_active_stations),
                        fontFamily = BerylFontFamily,
                        fontSize = 12.sp,
                        color = Color.Black
                    )
                }
            }
            Spacer(modifier = Modifier.height(12.dp))
            BerylEnergyLegend()
        }

        Column(
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            Button(
                onClick = { viewModel.setEcoOptimized(true) },
                colors = ButtonDefaults.buttonColors(containerColor = BerylGreen),
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(20.dp)
            ) {
                Icon(imageVector = Icons.Outlined.Bolt, contentDescription = null, tint = Color.White)
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = stringResource(R.string.mobility_ecoroute),
                    fontFamily = BerylFontFamily,
                    fontSize = 16.sp,
                    color = Color.White
                )
            }
            Spacer(modifier = Modifier.height(8.dp))
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(Color(0xFFF1F4F2), RoundedCornerShape(14.dp))
                    .padding(horizontal = 12.dp, vertical = 10.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(imageVector = Icons.Outlined.Eco, contentDescription = null, tint = BerylGreen)
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = stringResource(R.string.mobility_estimated_savings),
                    fontFamily = BerylFontFamily,
                    fontSize = 12.sp,
                    color = Color.Black
                )
            }
        }
    }
}
