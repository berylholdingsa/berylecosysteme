package com.beryl.berylandroid.screens

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.foundation.Image
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.beryl.berylandroid.R
import com.beryl.berylandroid.viewmodel.berylpay.TransferViewModel
import java.text.NumberFormat
import java.util.Currency
import java.util.Locale

@Composable
fun ConfirmTransferScreen(
    viewModel: TransferViewModel = viewModel(),
    onBack: () -> Unit = {},
    onTransferCompleted: () -> Unit = {}
) {
    val state by viewModel.uiState.collectAsState()
    val beneficiary = state.selectedBeneficiary
    val amount = state.amountInput.toDoubleOrNull() ?: 0.0
    val fees = 0.0
    val finalAmount = amount + fees

    Surface(modifier = Modifier.fillMaxSize(), color = Color.Transparent) {
        Box(modifier = Modifier.fillMaxSize()) {
            Image(
                painter = painterResource(id = R.drawable.bg_berylpay_black_metal),
                contentDescription = null,
                modifier = Modifier.fillMaxSize(),
                contentScale = ContentScale.Crop
            )

            if (state.successTraceId != null) {
                TransferSuccessContent(
                    traceId = state.successTraceId.orEmpty(),
                    onDone = {
                        viewModel.clearSuccess()
                        onTransferCompleted()
                    }
                )
            } else {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(horizontal = 18.dp, vertical = 16.dp),
                    verticalArrangement = Arrangement.spacedBy(14.dp)
                ) {
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(28.dp),
                        colors = CardDefaults.cardColors(containerColor = Color.Transparent)
                    ) {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(170.dp)
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
                                    text = "Confirmation transfert",
                                    color = Color.White,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 22.sp
                                )
                                Text(
                                    text = "Montant final",
                                    color = Color.White.copy(alpha = 0.9f),
                                    fontSize = 14.sp
                                )
                                Text(
                                    text = formatCurrency(finalAmount, state.currency),
                                    color = Color.White,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 30.sp
                                )
                            }
                        }
                    }

                    if (beneficiary == null || amount <= 0.0) {
                        Card(
                            modifier = Modifier.fillMaxWidth(),
                            shape = RoundedCornerShape(20.dp),
                            colors = CardDefaults.cardColors(containerColor = Color(0x99111111))
                        ) {
                            Text(
                                text = "Informations de transfert incomplètes.",
                                modifier = Modifier.padding(16.dp),
                                color = Color(0xFFFFB4AB)
                            )
                        }
                    } else {
                        SummaryRow("Bénéficiaire", beneficiary.name)
                        SummaryRow("Compte", beneficiary.accountId)
                        SummaryRow("Montant", formatCurrency(amount, state.currency))
                        SummaryRow("Frais", formatCurrency(fees, state.currency))
                        SummaryRow(
                            label = "Total débité",
                            value = formatCurrency(finalAmount, state.currency),
                            valueColor = Color(0xFF37D67A)
                        )
                    }

                    if (!state.errorMessage.isNullOrBlank()) {
                        Card(
                            modifier = Modifier.fillMaxWidth(),
                            shape = RoundedCornerShape(16.dp),
                            colors = CardDefaults.cardColors(containerColor = Color(0x66B3261E))
                        ) {
                            Text(
                                text = state.errorMessage.orEmpty(),
                                modifier = Modifier.padding(12.dp),
                                color = Color(0xFFFFDAD6),
                                fontSize = 13.sp
                            )
                        }
                    }

                    Spacer(modifier = Modifier.weight(1f))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(10.dp)
                    ) {
                        OutlinedButton(
                            onClick = onBack,
                            modifier = Modifier
                                .weight(1f)
                                .height(52.dp),
                            shape = RoundedCornerShape(16.dp)
                        ) {
                            Text("Retour")
                        }
                        Button(
                            onClick = viewModel::confirmTransfer,
                            modifier = Modifier
                                .weight(1f)
                                .height(52.dp),
                            enabled = beneficiary != null && amount > 0.0 && !state.isSubmitting,
                            colors = ButtonDefaults.buttonColors(
                                containerColor = Color(0xFF014421),
                                contentColor = Color.White,
                                disabledContainerColor = Color(0xFF014421).copy(alpha = 0.45f)
                            ),
                            shape = RoundedCornerShape(16.dp)
                        ) {
                            Text("Confirmer", fontWeight = FontWeight.SemiBold)
                        }
                    }
                }
            }

            if (state.isSubmitting) {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .clickable(enabled = false) {}
                        .padding(24.dp),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator(color = Color.White)
                }
            }
        }
    }
}

@Composable
private fun SummaryRow(
    label: String,
    value: String,
    valueColor: Color = Color.White
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0x99111111))
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 14.dp, vertical = 12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(text = label, color = Color.White.copy(alpha = 0.85f), fontSize = 13.sp)
            Text(text = value, color = valueColor, fontWeight = FontWeight.SemiBold, fontSize = 14.sp)
        }
    }
}

@Composable
private fun TransferSuccessContent(
    traceId: String,
    onDone: () -> Unit
) {
    AnimatedVisibility(
        visible = true,
        enter = fadeIn(animationSpec = tween(durationMillis = 280))
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 24.dp),
            contentAlignment = Alignment.Center
        ) {
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(24.dp),
                colors = CardDefaults.cardColors(containerColor = Color(0xFF101010))
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 20.dp, vertical = 24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    androidx.compose.material3.Icon(
                        imageVector = Icons.Filled.CheckCircle,
                        contentDescription = null,
                        tint = Color(0xFF37D67A)
                    )
                    Text(
                        text = "Transaction confirmée",
                        color = Color.White,
                        fontWeight = FontWeight.Bold,
                        fontSize = 20.sp
                    )
                    Text(
                        text = "Trace ID: $traceId",
                        color = Color.White.copy(alpha = 0.9f),
                        textAlign = TextAlign.Center
                    )
                    Button(
                        onClick = onDone,
                        colors = ButtonDefaults.buttonColors(
                            containerColor = Color(0xFF014421),
                            contentColor = Color.White
                        ),
                        shape = RoundedCornerShape(14.dp)
                    ) {
                        Text("Retour BerylPay")
                    }
                }
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
