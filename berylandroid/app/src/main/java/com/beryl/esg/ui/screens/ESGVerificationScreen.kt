package com.beryl.esg.ui.screens

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.tooling.preview.Preview
import androidx.lifecycle.viewmodel.compose.viewModel
import com.beryl.esg.ui.components.ESGBooleanValue
import com.beryl.esg.ui.components.ESGPremiumCard
import com.beryl.esg.ui.components.ESGPremiumScreen
import com.beryl.esg.ui.components.ESGPrimaryValue
import com.beryl.esg.ui.components.ESGSectionTitle
import com.beryl.esg.ui.components.ESGStateRenderer
import com.beryl.esg.ui.state.ESGUiState
import com.beryl.esg.ui.state.ESGVerificationContent
import com.beryl.esg.ui.state.ESGViewModel

@Composable
fun ESGVerificationScreen(
    tripId: String,
    onBack: () -> Unit,
    viewModel: ESGViewModel = viewModel()
) {
    val state by viewModel.verificationState.collectAsState()

    LaunchedEffect(tripId) {
        viewModel.loadVerification(tripId)
    }

    ESGVerificationBody(
        state = state,
        tripId = tripId,
        onBack = onBack,
        onRetry = { viewModel.loadVerification(tripId) }
    )
}

@Composable
private fun ESGVerificationBody(
    state: ESGUiState<ESGVerificationContent>,
    tripId: String,
    onBack: () -> Unit,
    onRetry: () -> Unit
) {
    ESGPremiumScreen(title = "Verification", onBack = onBack) {
        ESGStateRenderer(state = state, onRetry = onRetry) { content ->
            ESGPremiumCard {
                ESGSectionTitle("trip_id")
                ESGPrimaryValue(tripId)

                ESGSectionTitle("verified")
                ESGBooleanValue(content.verified)

                ESGSectionTitle("hash_valid")
                ESGBooleanValue(content.hashValid)

                ESGSectionTitle("signature_valid")
                ESGBooleanValue(content.signatureValid)

                ESGSectionTitle("asym_signature_valid")
                ESGBooleanValue(content.asymSignatureValid)
            }
        }
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF072015)
@Composable
private fun ESGVerificationScreenPreview() {
    ESGVerificationBody(
        state = ESGUiState.Content(
            ESGVerificationContent(
                verified = true,
                hashValid = true,
                signatureValid = true,
                asymSignatureValid = true
            )
        ),
        tripId = "trip-preview-1",
        onBack = {},
        onRetry = {}
    )
}
