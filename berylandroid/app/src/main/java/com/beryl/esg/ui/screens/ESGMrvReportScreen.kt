package com.beryl.esg.ui.screens

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.tooling.preview.Preview
import androidx.lifecycle.viewmodel.compose.viewModel
import com.beryl.esg.ui.components.ESGPremiumButton
import com.beryl.esg.ui.components.ESGPremiumCard
import com.beryl.esg.ui.components.ESGPremiumScreen
import com.beryl.esg.ui.components.ESGPrimaryValue
import com.beryl.esg.ui.components.ESGSecondaryLabel
import com.beryl.esg.ui.components.ESGSectionTitle
import com.beryl.esg.ui.components.ESGStateRenderer
import com.beryl.esg.ui.components.formatDecimal
import com.beryl.esg.ui.state.ESGMrvReportContent
import com.beryl.esg.ui.state.ESGUiState
import com.beryl.esg.ui.state.ESGViewModel

@Composable
fun ESGMrvReportScreen(
    onBack: () -> Unit,
    onOpenMethodology: () -> Unit,
    viewModel: ESGViewModel = viewModel()
) {
    val state by viewModel.mrvReportState.collectAsState()

    LaunchedEffect(Unit) {
        viewModel.loadMrvReport(period = "3M")
    }

    ESGMrvReportBody(
        state = state,
        onBack = onBack,
        onRetry = { viewModel.loadMrvReport(period = "3M") },
        onOpenMethodology = onOpenMethodology
    )
}

@Composable
private fun ESGMrvReportBody(
    state: ESGUiState<ESGMrvReportContent>,
    onBack: () -> Unit,
    onRetry: () -> Unit,
    onOpenMethodology: () -> Unit
) {
    ESGPremiumScreen(title = "MRV Report", onBack = onBack) {
        ESGStateRenderer(state = state, onRetry = onRetry) { content ->
            ESGPremiumCard {
                ESGSectionTitle("total_co2_avoided")
                ESGPrimaryValue(formatDecimal(content.totalCo2Avoided))

                ESGSectionTitle("methodology_version")
                ESGPrimaryValue(content.methodologyVersion)

                ESGSectionTitle("average_confidence")
                ESGPrimaryValue(formatDecimal(content.averageConfidence))

                ESGSectionTitle("aoq_status")
                ESGPrimaryValue(content.aoqStatus)

                ESGSecondaryLabel("period=3M")
            }
        }

        ESGPremiumButton(
            text = "Open Methodology",
            onClick = onOpenMethodology
        )
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF072015)
@Composable
private fun ESGMrvReportScreenPreview() {
    ESGMrvReportBody(
        state = ESGUiState.Content(
            ESGMrvReportContent(
                totalCo2Avoided = 17.512,
                methodologyVersion = "MRV-2026.1",
                averageConfidence = 93.0,
                aoqStatus = "PASS"
            )
        ),
        onBack = {},
        onRetry = {},
        onOpenMethodology = {}
    )
}
