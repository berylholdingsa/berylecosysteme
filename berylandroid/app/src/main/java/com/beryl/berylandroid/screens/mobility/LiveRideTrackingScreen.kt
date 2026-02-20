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
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.AddIcCall
import androidx.compose.material.icons.outlined.PersonPin
import androidx.compose.material.icons.outlined.Share
import androidx.compose.material.icons.outlined.Timer
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.beryl.berylandroid.R
import com.beryl.berylandroid.ui.theme.BerylGreen
import com.beryl.berylandroid.viewmodel.mobility.MobilityViewModel

@Composable
fun LiveRideTrackingScreen(
    viewModel: MobilityViewModel
) {
    val state by viewModel.uiState.collectAsState()
    Box(modifier = Modifier.fillMaxSize()) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            BerylSectionCard(modifier = Modifier.fillMaxWidth()) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(imageVector = Icons.Outlined.Timer, contentDescription = null, tint = BerylGreen)
                    Spacer(modifier = Modifier.width(8.dp))
                    Column {
                        Text(
                            text = stringResource(R.string.mobility_eta_title),
                            fontFamily = BerylFontFamily,
                            fontSize = 12.sp,
                            color = Color.Black.copy(alpha = 0.6f)
                        )
                        Text(
                            text = stringResource(R.string.mobility_eta_minutes_format, state.etaMinutes),
                            fontFamily = BerylFontFamily,
                            fontWeight = FontWeight.SemiBold,
                            fontSize = 18.sp
                        )
                    }
                    Spacer(modifier = Modifier.weight(1f))
                    BerylCircularHalo(
                        modifier = Modifier.size(62.dp),
                        progress = 0.68f
                    )
                }
            }
            Spacer(modifier = Modifier.height(12.dp))
            BerylSectionCard(modifier = Modifier.fillMaxWidth()) {
                BerylTitle(text = stringResource(R.string.mobility_contract_title))
                Spacer(modifier = Modifier.height(8.dp))
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    BerylContractStep(label = stringResource(R.string.mobility_step_departure_confirmed), active = true)
                    BerylContractStep(
                        label = stringResource(R.string.mobility_step_en_route_format, state.nearestVehicle),
                        active = true
                    )
                    BerylContractStep(label = stringResource(R.string.mobility_step_arrival_predicted), active = false)
                }
            }
        }

        Column(
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Button(
                    onClick = {},
                    colors = ButtonDefaults.buttonColors(containerColor = BerylGreen),
                    modifier = Modifier.weight(1f).height(52.dp),
                    shape = RoundedCornerShape(16.dp)
                ) {
                    Icon(imageVector = Icons.Outlined.AddIcCall, contentDescription = null, tint = Color.White)
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = stringResource(R.string.mobility_emergency),
                        fontFamily = BerylFontFamily,
                        fontSize = 14.sp,
                        color = Color.White
                    )
                }
                Button(
                    onClick = {},
                    colors = ButtonDefaults.buttonColors(containerColor = Color.White, contentColor = BerylGreen),
                    modifier = Modifier.weight(1f).height(52.dp),
                    shape = RoundedCornerShape(16.dp)
                ) {
                    Icon(imageVector = Icons.Outlined.Share, contentDescription = null, tint = BerylGreen)
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = stringResource(R.string.mobility_share),
                        fontFamily = BerylFontFamily,
                        fontSize = 14.sp,
                        color = BerylGreen
                    )
                }
            }
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(Color(0xFFF1F4F2), RoundedCornerShape(16.dp))
                    .padding(horizontal = 12.dp, vertical = 10.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(imageVector = Icons.Outlined.PersonPin, contentDescription = null, tint = BerylGreen)
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = stringResource(R.string.mobility_arrival_point_format, "120 m"),
                    fontFamily = BerylFontFamily,
                    fontSize = 12.sp,
                    color = Color.Black
                )
            }
        }
    }
}
