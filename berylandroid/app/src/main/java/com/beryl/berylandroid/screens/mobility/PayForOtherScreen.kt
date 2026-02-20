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
import androidx.compose.material.icons.outlined.Badge
import androidx.compose.material.icons.outlined.Person
import androidx.compose.material.icons.outlined.Phone
import androidx.compose.material.icons.outlined.VolunteerActivism
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.OutlinedTextField
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
fun PayForOtherScreen(
    viewModel: MobilityViewModel
) {
    val state by viewModel.uiState.collectAsState()
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(18.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        BerylTitle(text = stringResource(R.string.mobility_pay_for_other_title))
        BerylSubtitle(text = stringResource(R.string.mobility_pay_for_other_subtitle))

        OutlinedTextField(
            value = state.passengerPhone,
            onValueChange = {},
            modifier = Modifier.fillMaxWidth(),
            leadingIcon = { Icon(imageVector = Icons.Outlined.Phone, contentDescription = null) },
            placeholder = { Text(stringResource(R.string.mobility_passenger_placeholder), fontFamily = BerylFontFamily) }
        )

        BerylSectionCard(modifier = Modifier.fillMaxWidth()) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(40.dp)
                        .background(BerylGreen.copy(alpha = 0.12f), CircleShape),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(imageVector = Icons.Outlined.Person, contentDescription = null, tint = BerylGreen)
                }
                Spacer(modifier = Modifier.width(12.dp))
                Column {
                    Text(
                        text = state.passengerName,
                        fontFamily = BerylFontFamily,
                        fontWeight = FontWeight.SemiBold,
                        fontSize = 16.sp
                    )
                    Text(
                        text = stringResource(R.string.mobility_trip_status),
                        fontFamily = BerylFontFamily,
                        fontSize = 12.sp,
                        color = Color.Black.copy(alpha = 0.6f)
                    )
                }
                Spacer(modifier = Modifier.weight(1f))
                BerylPill(text = stringResource(R.string.mobility_sponsored_trip))
            }
            Spacer(modifier = Modifier.height(14.dp))
            BerylConnectionLink(modifier = Modifier.fillMaxWidth().height(36.dp))
            Spacer(modifier = Modifier.height(10.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(imageVector = Icons.Outlined.Badge, contentDescription = null, tint = BerylGreen)
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = stringResource(R.string.mobility_notification_sent),
                    fontFamily = BerylFontFamily,
                    fontSize = 12.sp,
                    color = Color.Black.copy(alpha = 0.6f)
                )
            }
        }

        Box(modifier = Modifier.weight(1f)) {
            Box(
                modifier = Modifier
                    .align(Alignment.TopStart)
                    .padding(12.dp)
                    .background(Color(0xFFF1F4F2), RoundedCornerShape(16.dp))
                    .padding(horizontal = 12.dp, vertical = 8.dp)
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(imageVector = Icons.Outlined.VolunteerActivism, contentDescription = null, tint = BerylGreen)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = stringResource(R.string.mobility_taxi_live_format, state.passengerName),
                        fontFamily = BerylFontFamily,
                        fontSize = 12.sp
                    )
                }
            }
        }

        Button(
            onClick = {},
            modifier = Modifier.fillMaxWidth().height(54.dp),
            colors = ButtonDefaults.buttonColors(containerColor = BerylGreen),
            shape = RoundedCornerShape(20.dp)
        ) {
            Text(
                text = stringResource(R.string.mobility_fund_trip),
                fontFamily = BerylFontFamily,
                fontSize = 16.sp,
                color = Color.White
            )
        }
    }
}
