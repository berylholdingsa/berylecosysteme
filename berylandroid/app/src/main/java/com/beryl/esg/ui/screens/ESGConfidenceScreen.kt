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
import com.beryl.esg.ui.state.ESGConfidenceContent
import com.beryl.esg.ui.state.ESGUiState
import com.beryl.esg.ui.state.ESGViewModel

@Composable
fun ESGConfidenceScreen(
    tripId: String,
    onBack: () -> Unit,
    onOpenVerification: (String) -> Unit,
    viewModel: ESGViewModel = viewModel()
) {
    val state by viewModel.confidenceState.collectAsState()

    LaunchedEffect(tripId) {
        viewModel.loadConfidence(tripId)
    }

    ESGConfidenceBody(
        state = state,
        tripId = tripId,
        onBack = onBack,
        onRetry = { viewModel.loadConfidence(tripId) },
        onOpenVerification = onOpenVerification
    )
}

@Composable
private fun ESGConfidenceBody(
    state: ESGUiState<ESGConfidenceContent>,
    tripId: String,
    onBack: () -> Unit,
    onRetry: () -> Unit,
    onOpenVerification: (String) -> Unit
) {
    ESGPremiumScreen(title = "Confidence", onBack = onBack) {
        ESGStateRenderer(state = state, onRetry = onRetry) { content ->
            ESGPremiumCard {
                ESGSectionTitle("trip_id")
                ESGPrimaryValue(tripId)

                ESGSectionTitle("confidence_score")
                ESGPrimaryValue(content.confidenceScore.toString())

                ESGSectionTitle("integrity_index")
                ESGPrimaryValue(content.integrityIndex.toString())

                ESGSectionTitle("aoq_status")
                ESGPrimaryValue(content.aoqStatus)

                ESGSectionTitle("anomaly_flags")
                if (content.anomalyFlags.isEmpty()) {
                    ESGSecondaryLabel("[]")
                } else {
                    content.anomalyFlags.forEach { flag ->
                        ESGSecondaryLabel(flag)
                    }
                }
            }
        }

        Column(
            modifier = androidx.compose.ui.Modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            ESGPremiumButton(
                text = "Open Verification",
                onClick = { onOpenVerification(tripId) }
            )
        }
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF072015)
@Composable
private fun ESGConfidenceScreenPreview() {
    ESGConfidenceBody(
        state = ESGUiState.Content(
            ESGConfidenceContent(
                confidenceScore = 96,
                integrityIndex = 99,
                aoqStatus = "PASS",
                anomalyFlags = listOf("PATTERN_DUPLICATION")
            )
        ),
        tripId = "trip-preview-1",
        onBack = {},
        onRetry = {},
        onOpenVerification = {}
    )
}
