package com.beryl.berylandroid.screens.mobility

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.Orientation
import androidx.compose.foundation.gestures.draggable
import androidx.compose.foundation.gestures.rememberDraggableState
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.CreditCard
import androidx.compose.material.icons.outlined.PhoneIphone
import androidx.compose.material.icons.outlined.Shield
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.beryl.berylandroid.R
import com.beryl.berylandroid.ui.theme.BerylGreen
import com.beryl.berylandroid.viewmodel.mobility.MobilityViewModel
import com.beryl.berylandroid.viewmodel.mobility.PaymentMethod
import com.beryl.berylandroid.viewmodel.mobility.PaymentStatus
import kotlin.math.roundToInt

@Composable
fun PayMyRideScreen(
    viewModel: MobilityViewModel
) {
    val state by viewModel.uiState.collectAsState()
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        BerylTitle(text = stringResource(R.string.mobility_pay_my_title))
        BerylSubtitle(text = stringResource(R.string.mobility_pay_my_subtitle))

        Box(modifier = Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
            AnimatedCircleOutline(modifier = Modifier.size(160.dp))
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    text = state.payAmount,
                    fontFamily = BerylFontFamily,
                    fontSize = 28.sp,
                    color = Color.Black
                )
                Text(
                    text = stringResource(R.string.mobility_impact_avoided_format, state.co2AvoidedKg),
                    fontFamily = BerylFontFamily,
                    fontSize = 12.sp,
                    color = Color.Black.copy(alpha = 0.6f)
                )
            }
        }

        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            PaymentOption(
                label = stringResource(R.string.mobility_payment_berylpay),
                icon = Icons.Outlined.Shield,
                selected = state.paymentMethod == PaymentMethod.BERYL_PAY,
                onClick = { viewModel.updatePaymentMethod(PaymentMethod.BERYL_PAY) }
            )
            PaymentOption(
                label = stringResource(R.string.mobility_payment_mobile_money),
                icon = Icons.Outlined.PhoneIphone,
                selected = state.paymentMethod == PaymentMethod.MOBILE_MONEY,
                onClick = { viewModel.updatePaymentMethod(PaymentMethod.MOBILE_MONEY) }
            )
            PaymentOption(
                label = stringResource(R.string.mobility_payment_card),
                icon = Icons.Outlined.CreditCard,
                selected = state.paymentMethod == PaymentMethod.CARD,
                onClick = { viewModel.updatePaymentMethod(PaymentMethod.CARD) }
            )
        }

        SlideToPay(
            modifier = Modifier.fillMaxWidth(),
            onPaid = viewModel::markPaid
        )

        if (state.paymentStatus == PaymentStatus.Confirmed) {
            Text(
                text = stringResource(R.string.mobility_payment_confirmed),
                fontFamily = BerylFontFamily,
                fontSize = 12.sp,
                color = BerylGreen
            )
        }
    }
}

@Composable
private fun PaymentOption(
    label: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    selected: Boolean,
    onClick: () -> Unit
) {
    val containerColor = if (selected) BerylGreen else Color.White
    val contentColor = if (selected) Color.White else BerylGreen
    Button(
        onClick = onClick,
        colors = ButtonDefaults.buttonColors(containerColor = containerColor, contentColor = contentColor),
        shape = RoundedCornerShape(18.dp),
        modifier = Modifier.height(44.dp)
    ) {
        Icon(imageVector = icon, contentDescription = null)
        Spacer(modifier = Modifier.width(6.dp))
        Text(text = label, fontFamily = BerylFontFamily, fontSize = 12.sp)
    }
}

@Composable
private fun SlideToPay(
    modifier: Modifier = Modifier,
    onPaid: () -> Unit
) {
    val trackHeight = 58.dp
    val knobSize = 46.dp
    var dragOffset by remember { mutableFloatStateOf(0f) }
    BoxWithConstraints(
        modifier = modifier
            .height(trackHeight)
            .clip(RoundedCornerShape(50))
            .background(Color(0xFFF1F4F2))
            .padding(horizontal = 6.dp),
        contentAlignment = Alignment.CenterStart
    ) {
        val maxOffsetPx = with(androidx.compose.ui.platform.LocalDensity.current) {
            (maxWidth - knobSize - 12.dp).toPx().coerceAtLeast(0f)
        }
        val draggableState = rememberDraggableState { delta ->
            dragOffset = (dragOffset + delta).coerceIn(0f, maxOffsetPx)
        }

        LaunchedEffect(dragOffset, maxOffsetPx) {
            if (maxOffsetPx > 0f && dragOffset >= maxOffsetPx * 0.85f) {
                onPaid()
            }
        }

        Text(
            text = stringResource(R.string.mobility_slide_to_pay),
            fontFamily = BerylFontFamily,
            fontSize = 14.sp,
            color = Color.Black.copy(alpha = 0.5f),
            modifier = Modifier.align(Alignment.Center)
        )
        Box(
            modifier = Modifier
                .offset { IntOffset(dragOffset.roundToInt(), 0) }
                .size(knobSize)
                .clip(CircleShape)
                .background(BerylGreen)
                .draggable(
                    state = draggableState,
                    orientation = Orientation.Horizontal
                ),
            contentAlignment = Alignment.Center
        ) {
            Canvas(modifier = Modifier.size(18.dp)) {
                drawLine(
                    color = Color.White,
                    start = Offset(0f, size.height / 2f),
                    end = Offset(size.width, size.height / 2f),
                    strokeWidth = 4f,
                    cap = StrokeCap.Round
                )
            }
        }
    }
}
