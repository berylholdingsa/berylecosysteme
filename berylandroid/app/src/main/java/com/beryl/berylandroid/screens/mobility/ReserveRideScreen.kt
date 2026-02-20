package com.beryl.berylandroid.screens.mobility

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
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.AutoAwesome
import androidx.compose.material.icons.outlined.Bolt
import androidx.compose.material.icons.outlined.Eco
import androidx.compose.material.icons.outlined.Navigation
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
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
fun ReserveRideScreen(
    viewModel: MobilityViewModel,
    onRequestRide: () -> Unit
) {
    val state by viewModel.uiState.collectAsState()
    Box(modifier = Modifier.fillMaxSize()) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 18.dp)
        ) {
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(22.dp),
                elevation = CardDefaults.cardElevation(12.dp),
                colors = CardDefaults.cardColors(containerColor = Color(0xFF014421))
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(imageVector = Icons.Outlined.AutoAwesome, contentDescription = null, tint = Color.White)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = stringResource(R.string.mobility_destination_smart),
                            fontFamily = BerylFontFamily,
                            fontSize = 13.sp,
                            color = Color.White
                        )
                    }
                    Spacer(modifier = Modifier.height(8.dp))
                    OutlinedTextField(
                        value = state.destinationQuery,
                        onValueChange = viewModel::updateDestination,
                        modifier = Modifier.fillMaxWidth(),
                        placeholder = {
                            Text(
                                stringResource(R.string.mobility_where_go),
                                fontFamily = BerylFontFamily,
                                color = Color.White
                            )
                        },
                        leadingIcon = {
                            Icon(
                                imageVector = Icons.Outlined.Navigation,
                                contentDescription = null,
                                tint = Color.White
                            )
                        },
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedTextColor = Color.White,
                            unfocusedTextColor = Color.White,
                            focusedPlaceholderColor = Color.White,
                            unfocusedPlaceholderColor = Color.White,
                            focusedLeadingIconColor = Color.White,
                            unfocusedLeadingIconColor = Color.White
                        )
                    )
                    Spacer(modifier = Modifier.height(10.dp))
                    LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        items(state.aiSuggestions.size) { index ->
                            val suggestion = state.aiSuggestions[index]
                            BerylStatChip(label = stringResource(R.string.mobility_ai_label), value = suggestion)
                        }
                    }
                    Spacer(modifier = Modifier.height(8.dp))
                    LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        items(state.frequentDestinations.size) { index ->
                            val item = state.frequentDestinations[index]
                            BerylStatChip(label = stringResource(R.string.mobility_recurring_label), value = item)
                        }
                    }
                }
            }
            Spacer(modifier = Modifier.height(12.dp))
            BerylSectionCard(modifier = Modifier.fillMaxWidth()) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(20.dp),
                    verticalArrangement = Arrangement.spacedBy(14.dp)
                ) {
                    BerylTitle(text = stringResource(R.string.mobility_preview_title))
                    BerylSubtitle(text = stringResource(R.string.mobility_preview_subtitle))
                    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                        BerylStatChip(label = stringResource(R.string.mobility_price), value = state.priceEstimate)
                        BerylStatChip(label = stringResource(R.string.mobility_time), value = "${state.etaMinutes} min")
                    }
                    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                        BerylStatChip(label = stringResource(R.string.mobility_range), value = "${state.remainingRangeKm} km")
                        BerylStatChip(label = stringResource(R.string.mobility_co2_avoided), value = "${state.co2AvoidedKg} kg")
                    }
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(imageVector = Icons.Outlined.Bolt, contentDescription = null, tint = BerylGreen)
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = stringResource(R.string.mobility_recommended_vehicle, state.recommendedVehicle),
                            fontFamily = BerylFontFamily,
                            fontSize = 13.sp,
                            color = Color.Black
                        )
                    }
                    Spacer(modifier = Modifier.height(8.dp))
                    Button(
                        onClick = onRequestRide,
                        colors = ButtonDefaults.buttonColors(containerColor = BerylGreen),
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(top = 12.dp, bottom = 8.dp),
                        shape = MaterialTheme.shapes.extraLarge
                    ) {
                        Icon(imageVector = Icons.Outlined.Eco, contentDescription = null, tint = Color.White)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = stringResource(R.string.mobility_request_vehicle),
                            fontFamily = BerylFontFamily,
                            fontSize = 16.sp,
                            fontWeight = FontWeight.SemiBold,
                            color = Color.White
                        )
                    }
                }
            }
        }

        Column(
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            Text(
                text = stringResource(R.string.mobility_map_hint),
                fontFamily = BerylFontFamily,
                fontSize = 11.sp,
                color = Color.Black.copy(alpha = 0.6f),
                modifier = Modifier.align(Alignment.CenterHorizontally)
            )
        }
    }
}
