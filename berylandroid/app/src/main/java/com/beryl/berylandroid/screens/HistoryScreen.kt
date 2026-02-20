package com.beryl.berylandroid.screens

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.scaleIn
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
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ContentCopy
import androidx.compose.material.icons.filled.ReceiptLong
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.beryl.berylandroid.R
import com.beryl.berylandroid.network.berylpay.TransactionDto
import com.beryl.berylandroid.viewmodel.berylpay.HistoryUiState
import com.beryl.berylandroid.viewmodel.berylpay.TransactionFilter
import com.beryl.berylandroid.viewmodel.berylpay.TransactionHistoryViewModel
import java.text.NumberFormat
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.util.Currency
import java.util.Locale

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HistoryScreen(
    viewModel: TransactionHistoryViewModel = viewModel()
) {
    val transactions by viewModel.transactions.collectAsState()
    val uiState by viewModel.uiState.collectAsState()
    val selectedFilter by viewModel.selectedFilter.collectAsState()
    val searchQuery by viewModel.searchQuery.collectAsState()
    val isRefreshing by viewModel.isRefreshing.collectAsState()
    val clipboardManager = LocalClipboardManager.current
    var selectedTransaction by remember { mutableStateOf<TransactionDto?>(null) }

    PullToRefreshBox(
        isRefreshing = isRefreshing,
        onRefresh = viewModel::refresh,
        modifier = Modifier.fillMaxSize()
    ) {
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
                        .padding(horizontal = 18.dp, vertical = 16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    HistoryHeaderCard(transactionsCount = transactions.size)
                    HistoryFilterControl(
                        selectedFilter = selectedFilter,
                        onFilterSelected = viewModel::onFilterSelected
                    )
                    OutlinedTextField(
                        value = searchQuery,
                        onValueChange = viewModel::onSearchQueryChanged,
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true,
                        label = { Text("Recherche") },
                        placeholder = { Text("Type, requestId ou identifiant") },
                        shape = RoundedCornerShape(14.dp)
                    )

                    when (val state = uiState) {
                        HistoryUiState.Loading -> {
                            HistoryLoadingShimmer(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .weight(1f)
                            )
                        }

                        is HistoryUiState.Error -> {
                            HistoryErrorState(
                                message = state.message,
                                onRetry = viewModel::retry,
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .weight(1f)
                            )
                        }

                        HistoryUiState.Empty -> {
                            HistoryEmptyState(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .weight(1f)
                            )
                        }

                        is HistoryUiState.Success -> {
                            LazyColumn(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .weight(1f),
                                verticalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                itemsIndexed(
                                    items = state.transactions,
                                    key = { _, item -> "${item.id}_${item.requestId}" }
                                ) { index, transaction ->
                                    AnimatedVisibility(
                                        visible = true,
                                        enter = fadeIn(
                                            animationSpec = tween(
                                                durationMillis = 260,
                                                delayMillis = (index * 35).coerceAtMost(280)
                                            )
                                        ) + scaleIn(
                                            initialScale = 0.98f,
                                            animationSpec = tween(durationMillis = 240)
                                        )
                                    ) {
                                        TransactionRow(
                                            transaction = transaction,
                                            onClick = { selectedTransaction = transaction }
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    selectedTransaction?.let { transaction ->
        ModalBottomSheet(
            onDismissRequest = { selectedTransaction = null },
            containerColor = Color(0xFF101010),
            contentColor = Color.White
        ) {
            TransactionDetailSheet(
                transaction = transaction,
                onCopyRequestId = {
                    clipboardManager.setText(AnnotatedString(transaction.requestId))
                },
                onClose = { selectedTransaction = null }
            )
        }
    }
}

@Composable
private fun HistoryHeaderCard(transactionsCount: Int) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(containerColor = Color.Transparent)
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(138.dp)
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
                    .padding(horizontal = 18.dp, vertical = 16.dp),
                verticalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                Text(
                    text = "Historique premium",
                    color = Color.White,
                    fontWeight = FontWeight.Bold,
                    fontSize = 22.sp
                )
                Text(
                    text = "Transactions analysées",
                    color = Color.White.copy(alpha = 0.9f),
                    fontSize = 13.sp
                )
                Text(
                    text = transactionsCount.toString(),
                    color = Color.White,
                    fontWeight = FontWeight.Bold,
                    fontSize = 30.sp
                )
            }
        }
    }
}

@Composable
private fun HistoryFilterControl(
    selectedFilter: TransactionFilter,
    onFilterSelected: (TransactionFilter) -> Unit
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        listOf(
            TransactionFilter.ALL to "Tous",
            TransactionFilter.CREDIT to "Crédit",
            TransactionFilter.DEBIT to "Débit"
        ).forEach { (filter, label) ->
            val selected = filter == selectedFilter
            if (selected) {
                Button(
                    onClick = { onFilterSelected(filter) },
                    modifier = Modifier.weight(1f),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color(0xFF014421),
                        contentColor = Color.White
                    ),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Text(text = label)
                }
            } else {
                OutlinedButton(
                    onClick = { onFilterSelected(filter) },
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Text(text = label)
                }
            }
        }
    }
}

@Composable
private fun TransactionRow(
    transaction: TransactionDto,
    onClick: () -> Unit
) {
    val isCredit = transaction.type.contains("CREDIT", ignoreCase = true)
    val isDebit = transaction.type.contains("DEBIT", ignoreCase = true)
    val amountColor = when {
        isCredit -> Color(0xFF37D67A)
        isDebit -> Color(0xFFFF6767)
        else -> Color.White
    }
    val signedAmount = when {
        isCredit -> "+${formatCurrency(transaction.amount, transaction.currency)}"
        isDebit -> "-${formatCurrency(transaction.amount, transaction.currency)}"
        else -> formatCurrency(transaction.amount, transaction.currency)
    }

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0x99111111))
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 14.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = transaction.type,
                    color = Color.White,
                    fontWeight = FontWeight.SemiBold,
                    fontSize = 14.sp
                )
                Text(
                    text = formatTransactionDate(transaction.createdAt),
                    color = Color.White.copy(alpha = 0.7f),
                    fontSize = 12.sp
                )
            }
            Text(
                text = signedAmount,
                color = amountColor,
                fontWeight = FontWeight.Bold,
                fontSize = 14.sp,
                textAlign = TextAlign.End
            )
        }
    }
}

@Composable
private fun TransactionDetailSheet(
    transaction: TransactionDto,
    onCopyRequestId: () -> Unit,
    onClose: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 18.dp, vertical = 12.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        Text(
            text = "Détail transaction",
            color = Color.White,
            fontWeight = FontWeight.Bold,
            fontSize = 20.sp
        )
        DetailLine(label = "Montant", value = formatCurrency(transaction.amount, transaction.currency))
        DetailLine(label = "Type", value = transaction.type)
        DetailLine(label = "Date", value = formatTransactionDate(transaction.createdAt))
        DetailLine(label = "RequestId", value = truncateRequestId(transaction.requestId))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            OutlinedButton(
                onClick = onCopyRequestId,
                modifier = Modifier.weight(1f),
                shape = RoundedCornerShape(12.dp)
            ) {
                Icon(imageVector = Icons.Filled.ContentCopy, contentDescription = null)
                Spacer(modifier = Modifier.width(6.dp))
                Text("Copier")
            }
            Button(
                onClick = onClose,
                modifier = Modifier.weight(1f),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xFF014421),
                    contentColor = Color.White
                ),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text("Fermer")
            }
        }
        Spacer(modifier = Modifier.height(8.dp))
    }
}

@Composable
private fun DetailLine(label: String, value: String) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0x99171717))
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 12.dp, vertical = 10.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = label,
                color = Color.White.copy(alpha = 0.8f),
                fontSize = 12.sp
            )
            Text(
                text = value,
                color = Color.White,
                fontWeight = FontWeight.SemiBold,
                fontSize = 13.sp
            )
        }
    }
}

@Composable
private fun HistoryEmptyState(modifier: Modifier = Modifier) {
    Box(
        modifier = modifier,
        contentAlignment = Alignment.Center
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Icon(
                imageVector = Icons.Filled.ReceiptLong,
                contentDescription = null,
                tint = Color.White.copy(alpha = 0.78f)
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = "Aucune transaction trouvée",
                color = Color.White.copy(alpha = 0.88f),
                fontWeight = FontWeight.SemiBold
            )
            Text(
                text = "Modifiez votre filtre ou votre recherche.",
                color = Color.White.copy(alpha = 0.7f),
                fontSize = 12.sp
            )
        }
    }
}

@Composable
private fun HistoryErrorState(
    message: String,
    onRetry: () -> Unit,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier,
        contentAlignment = Alignment.Center
    ) {
        Card(
            shape = RoundedCornerShape(14.dp),
            colors = CardDefaults.cardColors(containerColor = Color(0x99141414))
        ) {
            Column(
                modifier = Modifier.padding(horizontal = 18.dp, vertical = 14.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                Text(
                    text = "Échec du chargement",
                    color = Color.White,
                    fontWeight = FontWeight.SemiBold
                )
                Text(
                    text = message,
                    color = Color.White.copy(alpha = 0.8f),
                    fontSize = 12.sp,
                    textAlign = TextAlign.Center
                )
                Button(
                    onClick = onRetry,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color(0xFF014421),
                        contentColor = Color.White
                    ),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Text("Réessayer")
                }
            }
        }
    }
}

@Composable
private fun HistoryLoadingShimmer(modifier: Modifier = Modifier) {
    val transition = rememberInfiniteTransition(label = "historyShimmer")
    val alpha by transition.animateFloat(
        initialValue = 0.35f,
        targetValue = 0.8f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 900),
            repeatMode = RepeatMode.Reverse
        ),
        label = "historyShimmerAlpha"
    )
    LazyColumn(
        modifier = modifier,
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        items(6) {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .alpha(alpha),
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(containerColor = Color(0x99181818))
            ) {
                Spacer(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(66.dp)
                )
            }
        }
    }
}

private fun formatTransactionDate(createdAt: String): String {
    val formatter = DateTimeFormatter.ofPattern("dd MMM yyyy • HH:mm", Locale.getDefault())
    return runCatching {
        Instant.parse(createdAt)
            .atZone(ZoneId.systemDefault())
            .format(formatter)
    }.getOrElse { createdAt }
}

private fun truncateRequestId(value: String): String {
    val trimmed = value.trim()
    if (trimmed.length <= 20) {
        return trimmed
    }
    return "${trimmed.take(8)}...${trimmed.takeLast(8)}"
}

private fun formatCurrency(amount: Double, currency: String): String {
    val normalized = currency.trim().uppercase(Locale.ROOT)
    return runCatching {
        val formatter = NumberFormat.getCurrencyInstance(Locale.getDefault())
        formatter.currency = Currency.getInstance(normalized)
        formatter.format(amount)
    }.getOrElse {
        String.format(
            Locale.getDefault(),
            "%.2f %s",
            amount,
            normalized.ifBlank { "N/A" }
        )
    }
}
