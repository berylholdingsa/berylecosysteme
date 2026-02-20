package com.beryl.esg.ui.screens

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.tooling.preview.Preview
import androidx.lifecycle.viewmodel.compose.viewModel
import com.beryl.esg.ui.components.ESGPremiumCard
import com.beryl.esg.ui.components.ESGPremiumScreen
import com.beryl.esg.ui.components.ESGPrimaryValue
import com.beryl.esg.ui.components.ESGSectionTitle
import com.beryl.esg.ui.components.ESGStateRenderer
import com.beryl.esg.ui.state.ESGMethodologyContent
import com.beryl.esg.ui.state.ESGUiState
import com.beryl.esg.ui.state.ESGViewModel

@Composable
fun ESGMethodologyScreen(
    onBack: () -> Unit,
    viewModel: ESGViewModel = viewModel()
) {
    val state by viewModel.methodologyState.collectAsState()

    LaunchedEffect(Unit) {
        viewModel.loadMethodology()
    }

    ESGMethodologyBody(
        state = state,
        onBack = onBack,
        onRetry = { viewModel.loadMethodology() }
    )
}

@Composable
private fun ESGMethodologyBody(
    state: ESGUiState<ESGMethodologyContent>,
    onBack: () -> Unit,
    onRetry: () -> Unit
) {
    ESGPremiumScreen(title = "Methodology", onBack = onBack) {
        ESGStateRenderer(state = state, onRetry = onRetry) { content ->
            ESGPremiumCard {
                ESGSectionTitle("methodology_version")
                ESGPrimaryValue(content.methodologyVersion)

                ESGSectionTitle("emission_factor_source")
                ESGPrimaryValue(content.emissionFactorSource)

                ESGSectionTitle("geographic_scope")
                ESGPrimaryValue(content.geographicScope)

                ESGSectionTitle("status")
                ESGPrimaryValue(content.status)
            }
        }
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF072015)
@Composable
private fun ESGMethodologyScreenPreview() {
    ESGMethodologyBody(
        state = ESGUiState.Content(
            ESGMethodologyContent(
                methodologyVersion = "MRV-2026.1",
                emissionFactorSource = "GREENOS_COUNTRY_FACTORS_JSON",
                geographicScope = "CI,SN,KE",
                status = "ACTIVE"
            )
        ),
        onBack = {},
        onRetry = {}
    )
}
