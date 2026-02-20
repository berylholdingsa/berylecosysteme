package com.beryl.esg.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.beryl.esg.ui.components.ESGPremiumButton
import com.beryl.esg.ui.components.ESGPremiumCard
import com.beryl.esg.ui.components.ESGPremiumScreen
import com.beryl.esg.ui.components.ESGPrimaryValue
import com.beryl.esg.ui.components.ESGSecondaryLabel
import com.beryl.esg.ui.components.ESGSectionTitle
import com.beryl.esg.ui.components.ESGStateRenderer
import com.beryl.esg.ui.components.formatDecimal
import com.beryl.esg.ui.state.ESGImpactDetailContent
import com.beryl.esg.ui.state.ESGUiState
import com.beryl.esg.ui.state.ESGViewModel

@Composable
fun ESGImpactDetailScreen(
    tripId: String,
    onBack: () -> Unit,
    onOpenConfidence: (String) -> Unit,
    onOpenVerification: (String) -> Unit,
    viewModel: ESGViewModel = viewModel()
) {
    val state by viewModel.impactState.collectAsState()

    LaunchedEffect(tripId) {
        viewModel.loadImpact(tripId)
    }

    ESGImpactDetailBody(
        state = state,
        tripId = tripId,
        onBack = onBack,
        onRetry = { viewModel.loadImpact(tripId) },
        onOpenConfidence = onOpenConfidence,
        onOpenVerification = onOpenVerification
    )
}

@Composable
private fun ESGImpactDetailBody(
    state: ESGUiState<ESGImpactDetailContent>,
    tripId: String,
    onBack: () -> Unit,
    onRetry: () -> Unit,
    onOpenConfidence: (String) -> Unit,
    onOpenVerification: (String) -> Unit
) {
    ESGPremiumScreen(title = "Impact Detail", onBack = onBack) {
        ESGStateRenderer(state = state, onRetry = onRetry) { content ->
            ESGPremiumCard {
                ESGSectionTitle("trip_id")
                ESGPrimaryValue(tripId)

                ESGSectionTitle("co2_avoided_kg")
                ESGPrimaryValue(formatDecimal(content.co2AvoidedKg))

                ESGSectionTitle("distance_km")
                ESGPrimaryValue(formatDecimal(content.distanceKm))

                ESGSectionTitle("country_code")
                ESGPrimaryValue(content.countryCode)

                ESGSectionTitle("event_hash")
                ESGSecondaryLabel(content.eventHash)

                ESGSectionTitle("signature_algorithm")
                ESGPrimaryValue(content.signatureAlgorithm)

                ESGSectionTitle("model_version")
                ESGPrimaryValue(content.modelVersion)
            }
        }

        Column(
            modifier = androidx.compose.ui.Modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            ESGPremiumButton(
                text = "Open Confidence",
                onClick = { onOpenConfidence(tripId) }
            )
            ESGPremiumButton(
                text = "Open Verification",
                onClick = { onOpenVerification(tripId) }
            )
        }
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF072015)
@Composable
private fun ESGImpactDetailScreenPreview() {
    ESGImpactDetailBody(
        state = ESGUiState.Content(
            ESGImpactDetailContent(
                co2AvoidedKg = 1.656,
                distanceKm = 12.0,
                countryCode = "CI",
                eventHash = "e3f758871b0556fc678e43aa08f4436f47fe7f79516b9a47a5d5a6837986a3b8",
                signatureAlgorithm = "HMAC-SHA256",
                modelVersion = "greenos-co2-v1"
            )
        ),
        tripId = "trip-preview-1",
        onBack = {},
        onRetry = {},
        onOpenConfidence = {},
        onOpenVerification = {}
    )
}
