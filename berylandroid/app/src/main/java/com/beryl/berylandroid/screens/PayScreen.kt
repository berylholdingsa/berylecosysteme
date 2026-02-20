package com.beryl.berylandroid.screens

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.animateContentSize
import androidx.compose.animation.core.animateDpAsState
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.scaleIn
import androidx.compose.foundation.Image
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.BorderStroke
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.beryl.berylandroid.R
import com.beryl.berylandroid.viewmodel.berylpay.BerylPayEvent
import com.beryl.berylandroid.viewmodel.berylpay.BerylPayUiState
import com.beryl.berylandroid.viewmodel.berylpay.BerylPayViewModel
import kotlinx.coroutines.flow.collectLatest
import java.text.SimpleDateFormat
import java.text.NumberFormat
import java.util.Currency
import java.util.Date
import java.util.Locale

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PayScreen(
    viewModel: BerylPayViewModel = viewModel(),
    onNavigateToLogin: () -> Unit = {},
    onNavigateToTransfer: () -> Unit = {},
    onNavigateToHistory: () -> Unit = {},
    transferCompleted: Boolean = false,
    onTransferRefreshConsumed: () -> Unit = {}
) {
    val state by viewModel.uiState.collectAsState()
    val isRefreshing by viewModel.isRefreshing.collectAsState()
    var isBalanceVisible by remember { mutableStateOf(true) }
    var selectedAction by rememberSaveable { mutableIntStateOf(0) }
    var showPremiumBlocks by remember { mutableStateOf(false) }

    LaunchedEffect(viewModel) {
        viewModel.events.collectLatest { event ->
            if (event is BerylPayEvent.NavigateToLogin) {
                onNavigateToLogin()
            }
        }
    }
    LaunchedEffect(Unit) {
        showPremiumBlocks = true
    }
    LaunchedEffect(transferCompleted) {
        if (transferCompleted) {
            viewModel.refreshBalance()
            onTransferRefreshConsumed()
        }
    }

    PullToRefreshBox(
        isRefreshing = isRefreshing,
        onRefresh = viewModel::refreshBalance,
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
                        .padding(horizontal = 18.dp, vertical = 16.dp)
                ) {
                    when (val uiState = state) {
                        BerylPayUiState.Loading -> {
                            Box(
                                modifier = Modifier.fillMaxSize(),
                                contentAlignment = Alignment.Center
                            ) {
                                CircularProgressIndicator(color = Color.White)
                            }
                        }

                        is BerylPayUiState.Success -> {
                            AnimatedVisibility(
                                visible = showPremiumBlocks,
                                enter = fadeIn(animationSpec = tween(durationMillis = 450))
                            ) {
                                MainBalanceCard(
                                    balance = uiState.balance,
                                    currency = uiState.currency,
                                    isBalanceVisible = isBalanceVisible,
                                    onToggleBalanceVisibility = { isBalanceVisible = !isBalanceVisible },
                                    isRefreshing = isRefreshing,
                                    selectedAction = selectedAction,
                                    onSelectAction = { selectedAction = it },
                                    onTransferClick = onNavigateToTransfer
                                )
                            }
                            Spacer(modifier = Modifier.height(16.dp))
                            AnimatedVisibility(
                                visible = showPremiumBlocks,
                                enter = fadeIn(animationSpec = tween(durationMillis = 300, delayMillis = 120)) +
                                    scaleIn(animationSpec = tween(durationMillis = 320, delayMillis = 120))
                            ) {
                                StrategicMiniCards()
                            }
                            Spacer(modifier = Modifier.height(18.dp))
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(
                                    text = "Activité récente",
                                    color = Color.White,
                                    fontSize = 20.sp,
                                    fontWeight = FontWeight.SemiBold
                                )
                                TextButton(onClick = onNavigateToHistory) {
                                    Text(
                                        text = "Voir tout",
                                        color = Color.White
                                    )
                                }
                            }
                            Spacer(modifier = Modifier.height(10.dp))
                            RecentActivityList(
                                modifier = Modifier.weight(1f),
                                activityItems = buildRecentActivity(uiState.balance, uiState.currency)
                            )
                        }

                        is BerylPayUiState.Error -> {
                            Box(
                                modifier = Modifier.fillMaxSize(),
                                contentAlignment = Alignment.Center
                            ) {
                                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                    Text(
                                        text = uiState.message,
                                        color = Color(0xFFFFB4AB),
                                        textAlign = TextAlign.Center
                                    )
                                    Spacer(modifier = Modifier.height(8.dp))
                                    TextButton(onClick = viewModel::loadBalance) {
                                        Text(stringResource(R.string.kyc_retry), color = Color.White)
                                    }
                                }
                            }
                        }

                        BerylPayUiState.SessionExpired -> {
                            Box(
                                modifier = Modifier.fillMaxSize(),
                                contentAlignment = Alignment.Center
                            ) {
                                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                    Text(
                                        text = "Session expirée. Veuillez vous reconnecter.",
                                        color = Color(0xFFFFB4AB),
                                        textAlign = TextAlign.Center
                                    )
                                    Spacer(modifier = Modifier.height(8.dp))
                                    TextButton(onClick = onNavigateToLogin) {
                                        Text("Se reconnecter", color = Color.White)
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun MainBalanceCard(
    balance: Double,
    currency: String,
    isBalanceVisible: Boolean,
    onToggleBalanceVisibility: () -> Unit,
    isRefreshing: Boolean,
    selectedAction: Int,
    onSelectAction: (Int) -> Unit,
    onTransferClick: () -> Unit
) {
    val actions = listOf("Transférer", "Payer", "Banque", "Facture")
    val actionGreen = Color(0xFF014421)
    val depthOffset by animateDpAsState(
        targetValue = if (isRefreshing) 2.dp else (-2).dp,
        label = "mainCardDepth"
    )
    val shadowElevation = 18.dp + depthOffset

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .shadow(
                elevation = shadowElevation,
                shape = androidx.compose.foundation.shape.RoundedCornerShape(28.dp),
                clip = false
            ),
        shape = androidx.compose.foundation.shape.RoundedCornerShape(28.dp),
        colors = CardDefaults.cardColors(containerColor = Color.Transparent)
    ) {
        Box(
            modifier = Modifier.fillMaxWidth()
        ) {
            Image(
                painter = painterResource(id = R.drawable.card_berylpay_green_metal),
                contentDescription = null,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(260.dp),
                contentScale = ContentScale.Crop
            )
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(260.dp)
                    .padding(20.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(
                        text = "Solde disponible",
                        color = Color.White.copy(alpha = 0.95f),
                        fontSize = 14.sp
                    )
                    IconButton(onClick = onToggleBalanceVisibility) {
                        Icon(
                            imageVector = if (isBalanceVisible) Icons.Filled.Visibility else Icons.Filled.VisibilityOff,
                            contentDescription = if (isBalanceVisible) "Masquer le solde" else "Afficher le solde",
                            tint = Color.White
                        )
                    }
                }
                Spacer(modifier = Modifier.height(10.dp))
                Text(
                    text = if (isBalanceVisible) {
                        formatCurrency(balance = balance, currency = currency)
                    } else {
                        "••••••"
                    },
                    fontWeight = FontWeight.Bold,
                    fontSize = 34.sp,
                    color = Color.White,
                    modifier = Modifier.animateContentSize()
                )
                Spacer(modifier = Modifier.weight(1f))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    actions.forEachIndexed { index, label ->
                        val isSelected = selectedAction == index
                        val interactionSource = remember { MutableInteractionSource() }
                        val isPressed by interactionSource.collectIsPressedAsState()
                        val scale by animateFloatAsState(
                            targetValue = if (isPressed) 0.96f else 1f,
                            label = "actionButtonScale"
                        )
                        val onActionClick = {
                            onSelectAction(index)
                            if (index == 0) {
                                onTransferClick()
                            }
                        }
                        if (isSelected) {
                            Button(
                                onClick = onActionClick,
                                interactionSource = interactionSource,
                                modifier = Modifier
                                    .weight(1f)
                                    .height(40.dp)
                                    .graphicsLayer(scaleX = scale, scaleY = scale),
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = actionGreen,
                                    contentColor = Color.White
                                )
                            ) {
                                Text(
                                    text = label,
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.SemiBold
                                )
                            }
                        } else {
                            OutlinedButton(
                                onClick = onActionClick,
                                interactionSource = interactionSource,
                                modifier = Modifier
                                    .weight(1f)
                                    .height(40.dp)
                                    .graphicsLayer(scaleX = scale, scaleY = scale),
                                colors = ButtonDefaults.outlinedButtonColors(
                                    containerColor = Color.White,
                                    contentColor = actionGreen
                                ),
                                border = BorderStroke(1.dp, actionGreen)
                            ) {
                                Text(
                                    text = label,
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.SemiBold
                                )
                            }
                        }
                    }
                }
                Spacer(modifier = Modifier.height(6.dp))
            }
        }
    }
}

@Composable
private fun StrategicMiniCards() {
    val items = listOf("Coffre Fort", "Tontine", "Diaspora", "PME")
    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            items.take(2).forEach { title ->
                StrategicMiniCard(title = title, modifier = Modifier.weight(1f))
            }
        }
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            items.drop(2).forEach { title ->
                StrategicMiniCard(title = title, modifier = Modifier.weight(1f))
            }
        }
    }
}

@Composable
private fun StrategicMiniCard(title: String, modifier: Modifier = Modifier) {
    Card(
        modifier = modifier,
        shape = androidx.compose.foundation.shape.RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(containerColor = Color.Transparent)
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(86.dp)
        ) {
            Image(
                painter = painterResource(id = R.drawable.card_black_metal_premium),
                contentDescription = null,
                modifier = Modifier.fillMaxSize(),
                contentScale = ContentScale.Crop
            )
            Text(
                text = title,
                color = Color.White,
                fontWeight = FontWeight.SemiBold,
                fontSize = 16.sp,
                modifier = Modifier
                    .align(Alignment.CenterStart)
                    .padding(start = 14.dp)
            )
        }
    }
}

@Composable
private fun RecentActivityList(
    activityItems: List<ActivityUiModel>,
    modifier: Modifier = Modifier
) {
    LazyColumn(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        items(activityItems) { item ->
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = item.type,
                        color = Color.White,
                        fontWeight = FontWeight.SemiBold,
                        fontSize = 14.sp
                    )
                    Text(
                        text = item.dateLabel,
                        color = Color.White.copy(alpha = 0.7f),
                        fontSize = 12.sp
                    )
                }
                Text(
                    text = item.amountLabel,
                    color = if (item.type == "CREDIT") Color(0xFF37D67A) else Color(0xFFFF6767),
                    fontWeight = FontWeight.Bold,
                    fontSize = 14.sp,
                    textAlign = TextAlign.End
                )
            }
        }
    }
}

private data class ActivityUiModel(
    val type: String,
    val dateLabel: String,
    val amountLabel: String
)

private fun buildRecentActivity(balance: Double, currency: String): List<ActivityUiModel> {
    val now = System.currentTimeMillis()
    val oneDayMillis = 24 * 60 * 60 * 1000L
    return listOf(
        ActivityUiModel(
            type = "CREDIT",
            dateLabel = formatActivityDate(now),
            amountLabel = "+${formatCurrency(balance * 0.15, currency)}"
        ),
        ActivityUiModel(
            type = "DEBIT",
            dateLabel = formatActivityDate(now - oneDayMillis),
            amountLabel = "-${formatCurrency(balance * 0.08, currency)}"
        ),
        ActivityUiModel(
            type = "CREDIT",
            dateLabel = formatActivityDate(now - (2 * oneDayMillis)),
            amountLabel = "+${formatCurrency(balance * 0.11, currency)}"
        ),
        ActivityUiModel(
            type = "DEBIT",
            dateLabel = formatActivityDate(now - (3 * oneDayMillis)),
            amountLabel = "-${formatCurrency(balance * 0.04, currency)}"
        )
    )
}

private fun formatActivityDate(timestamp: Long): String {
    val formatter = SimpleDateFormat("dd MMM yyyy • HH:mm", Locale.getDefault())
    return formatter.format(Date(timestamp))
}

private fun formatCurrency(balance: Double, currency: String): String {
    val normalizedCode = currency.trim().uppercase(Locale.ROOT)
    return runCatching {
        val formatter = NumberFormat.getCurrencyInstance(Locale.getDefault())
        formatter.currency = Currency.getInstance(normalizedCode)
        formatter.format(balance)
    }.getOrElse {
        String.format(
            Locale.getDefault(),
            "%.2f %s",
            balance,
            normalizedCode.ifBlank { "N/A" }
        )
    }
}
