package com.beryl.esg.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.weight
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.beryl.esg.data.repository.GreenOSRealtimeCalculateRequest
import com.beryl.esg.ui.components.ESGPremiumButton
import com.beryl.esg.ui.components.ESGPremiumCard
import com.beryl.esg.ui.components.ESGPremiumScreen
import com.beryl.esg.ui.components.ESGPrimaryValue
import com.beryl.esg.ui.components.ESGSecondaryLabel
import com.beryl.esg.ui.components.ESGSectionTitle
import com.beryl.esg.ui.components.ESGStateRenderer
import com.beryl.esg.ui.components.formatDecimal
import com.beryl.esg.ui.state.ESGHomeContent
import com.beryl.esg.ui.state.ESGUiState
import com.beryl.esg.ui.state.ESGViewModel

@Composable
fun ESGHomeScreen(
    onOpenImpactDetail: (String) -> Unit,
    onOpenConfidence: (String) -> Unit,
    onOpenVerification: (String) -> Unit,
    onOpenMrvReport: () -> Unit,
    onOpenMethodology: () -> Unit,
    activeTrip: GreenOSRealtimeCalculateRequest? = null,
    viewModel: ESGViewModel = viewModel()
) {
    val state by viewModel.homeState.collectAsState()
    var tripId by rememberSaveable { mutableStateOf("") }

    LaunchedEffect(activeTrip) {
        viewModel.loadHome(period = "3M", activeTrip = activeTrip)
    }

    ESGHomeBody(
        state = state,
        tripId = tripId,
        onTripIdChange = { tripId = it },
        onRetry = { viewModel.loadHome(period = "3M", activeTrip = activeTrip) },
        onOpenImpactDetail = onOpenImpactDetail,
        onOpenConfidence = onOpenConfidence,
        onOpenVerification = onOpenVerification,
        onOpenMrvReport = onOpenMrvReport,
        onOpenMethodology = onOpenMethodology
    )
}

@Composable
private fun ESGHomeBody(
    state: ESGUiState<ESGHomeContent>,
    tripId: String,
    onTripIdChange: (String) -> Unit,
    onRetry: () -> Unit,
    onOpenImpactDetail: (String) -> Unit,
    onOpenConfidence: (String) -> Unit,
    onOpenVerification: (String) -> Unit,
    onOpenMrvReport: () -> Unit,
    onOpenMethodology: () -> Unit
) {
    ESGPremiumScreen(title = "GreenOS ESG") {
        ESGStateRenderer(state = state, onRetry = onRetry) { content ->
            ESGPremiumCard {
                ESGSectionTitle("Dashboard 3M")
                ESGPrimaryValue("${formatDecimal(content.totalCo2Avoided)} kg CO2")
                ESGSecondaryLabel("total_co2_avoided")
                ESGPrimaryValue("${formatDecimal(content.totalDistance)} km")
                ESGSecondaryLabel("total_distance")
                ESGPrimaryValue(content.aoqStatus)
                ESGSecondaryLabel("aoq_status")
                ESGPrimaryValue(formatDecimal(content.averageConfidence))
                ESGSecondaryLabel("average_confidence")
                ESGSecondaryLabel("model_version: ${content.modelVersion}")
            }
        }

        ESGPremiumCard {
            ESGSectionTitle("Trip Query")
            OutlinedTextField(
                value = tripId,
                onValueChange = onTripIdChange,
                singleLine = true,
                label = { Text(text = "trip_id", color = Color.White.copy(alpha = 0.8f)) },
                modifier = Modifier.fillMaxWidth(),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = Color.White,
                    unfocusedBorderColor = Color.White.copy(alpha = 0.7f),
                    focusedTextColor = Color.White,
                    unfocusedTextColor = Color.White,
                    focusedLabelColor = Color.White.copy(alpha = 0.9f),
                    unfocusedLabelColor = Color.White.copy(alpha = 0.7f),
                    cursorColor = Color.White
                )
            )

            ESGPremiumButton(
                text = "Open Impact Detail",
                onClick = { onOpenImpactDetail(tripId.trim()) },
                enabled = tripId.isNotBlank()
            )

            ESGPremiumButton(
                text = "Open Confidence",
                onClick = { onOpenConfidence(tripId.trim()) },
                enabled = tripId.isNotBlank()
            )

            ESGPremiumButton(
                text = "Open Verification",
                onClick = { onOpenVerification(tripId.trim()) },
                enabled = tripId.isNotBlank()
            )
        }

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            ESGPremiumButton(
                text = "MRV Report",
                onClick = onOpenMrvReport,
                modifier = Modifier.weight(1f)
            )
            ESGPremiumButton(
                text = "Methodology",
                onClick = onOpenMethodology,
                modifier = Modifier.weight(1f)
            )
        }
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF072015)
@Composable
private fun ESGHomeScreenPreview() {
    var previewTripId by rememberSaveable { mutableStateOf("trip-preview-1") }
    ESGHomeBody(
        state = ESGUiState.Content(
            ESGHomeContent(
                totalCo2Avoided = 18.245,
                totalDistance = 126.572,
                aoqStatus = "PASS",
                averageConfidence = 92.0,
                modelVersion = "greenos-co2-v1"
            )
        ),
        tripId = previewTripId,
        onTripIdChange = { previewTripId = it },
        onRetry = {},
        onOpenImpactDetail = {},
        onOpenConfidence = {},
        onOpenVerification = {},
        onOpenMrvReport = {},
        onOpenMethodology = {}
    )
}
