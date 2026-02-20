package com.beryl.berylandroid.screens

import androidx.compose.foundation.Image
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.beryl.berylandroid.R
import com.beryl.berylandroid.viewmodel.berylpay.SavedBeneficiary
import com.beryl.berylandroid.viewmodel.berylpay.TransferViewModel
import java.text.NumberFormat
import java.time.Instant
import java.util.Currency
import java.util.Locale

@Composable
fun TransferScreen(
    currentBalance: Double = 0.0,
    currency: String = "XOF",
    onContinueToConfirm: () -> Unit = {},
    viewModel: TransferViewModel = viewModel()
) {
    val state by viewModel.uiState.collectAsState()
    val beneficiaries by viewModel.beneficiaries.collectAsState()
    val scrollState = rememberScrollState()
    val suggestions = remember(state.searchQuery, beneficiaries) {
        val normalizedQuery = state.searchQuery.trim()
        beneficiaries
            .sortedByDescending { parseLastUsedAtForUi(it.lastUsedAt) }
            .filter { beneficiary ->
                normalizedQuery.isBlank() ||
                    beneficiary.beneficiaryAccountId.contains(normalizedQuery, ignoreCase = true) ||
                    (beneficiary.nickname?.contains(normalizedQuery, ignoreCase = true) == true)
            }
            .take(5)
    }

    LaunchedEffect(currentBalance, currency) {
        viewModel.initializeBalance(currentBalance, currency)
    }

    Surface(modifier = Modifier.fillMaxSize(), color = Color.Transparent) {
        Box(modifier = Modifier.fillMaxSize()) {
            Image(
                painter = painterResource(id = R.drawable.bg_berylpay_black_metal),
                contentDescription = null,
                modifier = Modifier.fillMaxSize(),
                contentScale = ContentScale.Crop
            )

            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .verticalScroll(scrollState)
                    .padding(horizontal = 18.dp, vertical = 16.dp),
                verticalArrangement = Arrangement.spacedBy(14.dp)
            ) {
                TransferHeaderCard(
                    balance = state.balance,
                    currency = state.currency
                )

                OutlinedTextField(
                    value = state.searchQuery,
                    onValueChange = viewModel::onSearchQueryChanged,
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                    label = { Text("Compte bénéficiaire") },
                    placeholder = { Text("Saisir un compte") },
                    shape = RoundedCornerShape(16.dp)
                )

                if (state.showSuggestions && suggestions.isNotEmpty()) {
                    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        suggestions.forEach { beneficiary ->
                            val label = beneficiary.nickname?.trim()
                                ?.takeIf { it.isNotEmpty() }
                                ?: beneficiary.beneficiaryAccountId
                            val mapped = SavedBeneficiary(
                                id = beneficiary.id.ifBlank { beneficiary.beneficiaryAccountId },
                                name = label,
                                accountId = beneficiary.beneficiaryAccountId
                            )
                            val isSelected = state.selectedBeneficiary?.accountId == mapped.accountId
                            BeneficiaryRowCard(
                                beneficiary = mapped,
                                isSelected = isSelected,
                                onClick = { viewModel.selectBeneficiarySuggestion(beneficiary) }
                            )
                        }
                    }
                }

                OutlinedTextField(
                    value = state.amountInput,
                    onValueChange = viewModel::onAmountChanged,
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                    label = { Text("Montant") },
                    placeholder = { Text("0.00") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                    shape = RoundedCornerShape(16.dp)
                )

                if (!state.errorMessage.isNullOrBlank()) {
                    Text(
                        text = state.errorMessage.orEmpty(),
                        color = Color(0xFFFFB4AB),
                        fontSize = 13.sp
                    )
                }

                Button(
                    onClick = {
                        if (viewModel.canProceedToConfirmation()) {
                            onContinueToConfirm()
                        }
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(52.dp),
                    enabled = state.canContinue && !state.isSubmitting,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color(0xFF014421),
                        contentColor = Color.White,
                        disabledContainerColor = Color(0xFF014421).copy(alpha = 0.45f)
                    ),
                    shape = RoundedCornerShape(18.dp)
                ) {
                    Text("Continuer", fontWeight = FontWeight.SemiBold)
                }

                Spacer(modifier = Modifier.height(20.dp))
            }
        }
    }
}

@Composable
private fun TransferHeaderCard(balance: Double, currency: String) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(28.dp),
        colors = CardDefaults.cardColors(containerColor = Color.Transparent)
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(180.dp)
        ) {
            Image(
                painter = painterResource(id = R.drawable.card_berylpay_green_metal),
                contentDescription = null,
                modifier = Modifier.fillMaxSize(),
                contentScale = ContentScale.Crop
            )
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Text(
                    text = "Transfert",
                    color = Color.White,
                    fontWeight = FontWeight.Bold,
                    fontSize = 22.sp
                )
                Text(
                    text = "Solde disponible",
                    color = Color.White.copy(alpha = 0.9f),
                    fontSize = 14.sp
                )
                Text(
                    text = formatCurrency(balance, currency),
                    color = Color.White,
                    fontWeight = FontWeight.Bold,
                    fontSize = 32.sp
                )
            }
        }
    }
}

@Composable
private fun BeneficiaryRowCard(
    beneficiary: SavedBeneficiary,
    isSelected: Boolean,
    onClick: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        shape = RoundedCornerShape(18.dp),
        colors = CardDefaults.cardColors(containerColor = Color.Transparent),
        border = if (isSelected) {
            androidx.compose.foundation.BorderStroke(1.dp, Color(0xFF37D67A))
        } else {
            null
        }
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(74.dp)
        ) {
            Image(
                painter = painterResource(id = R.drawable.card_black_metal_premium),
                contentDescription = null,
                modifier = Modifier.fillMaxSize(),
                contentScale = ContentScale.Crop
            )
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = 14.dp, vertical = 12.dp),
                verticalArrangement = Arrangement.Center
            ) {
                Text(
                    text = beneficiary.name,
                    color = Color.White,
                    fontWeight = FontWeight.SemiBold,
                    fontSize = 15.sp
                )
                Text(
                    text = beneficiary.accountId,
                    color = Color.White.copy(alpha = 0.75f),
                    fontSize = 12.sp
                )
            }
        }
    }
}

private fun formatCurrency(value: Double, currency: String): String {
    val normalizedCode = currency.trim().uppercase(Locale.ROOT)
    return runCatching {
        val formatter = NumberFormat.getCurrencyInstance(Locale.getDefault())
        formatter.currency = Currency.getInstance(normalizedCode)
        formatter.format(value)
    }.getOrElse {
        String.format(
            Locale.getDefault(),
            "%.2f %s",
            value,
            normalizedCode.ifBlank { "N/A" }
        )
    }
}

private fun parseLastUsedAtForUi(value: String): Instant {
    return runCatching {
        Instant.parse(value)
    }.getOrElse {
        Instant.EPOCH
    }
}
