package com.beryl.berylandroid.screens.mobility

import androidx.compose.animation.core.InfiniteTransition
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.AssistChip
import androidx.compose.material3.AssistChipDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import com.mapbox.mapboxsdk.maps.MapView
import com.beryl.berylandroid.R
import com.beryl.berylandroid.ui.theme.BerylGreen

private val BerylInk = Color(0xFF0C0F0D)
private val BerylMuted = Color(0xFF5D6A63)
private val BerylSoft = Color(0xFFEFF3F0)

@Composable
fun BerylTitle(text: String, modifier: Modifier = Modifier) {
    Text(
        text = text,
        style = TextStyle(
            fontFamily = BerylFontFamily,
            fontWeight = FontWeight.SemiBold,
            fontSize = 20.sp,
            color = BerylInk
        ),
        modifier = modifier,
        maxLines = 1,
        overflow = TextOverflow.Ellipsis
    )
}

@Composable
fun BerylSubtitle(text: String, modifier: Modifier = Modifier) {
    Text(
        text = text,
        style = TextStyle(
            fontFamily = BerylFontFamily,
            fontWeight = FontWeight.Medium,
            fontSize = 13.sp,
            color = BerylMuted
        ),
        modifier = modifier
    )
}

@Composable
fun BerylStatChip(label: String, value: String, modifier: Modifier = Modifier) {
    AssistChip(
        onClick = {},
        label = {
            Column {
                Text(label, fontSize = 10.sp, color = BerylMuted, fontFamily = BerylFontFamily)
                Text(value, fontSize = 13.sp, color = BerylInk, fontFamily = BerylFontFamily, fontWeight = FontWeight.SemiBold)
            }
        },
        colors = AssistChipDefaults.assistChipColors(
            containerColor = BerylSoft,
            labelColor = BerylInk
        ),
        modifier = modifier
    )
}

@Composable
fun BerylSectionCard(modifier: Modifier = Modifier, content: @Composable () -> Unit) {
    Card(
        modifier = modifier,
        colors = CardDefaults.cardColors(containerColor = Color.White),
        elevation = CardDefaults.cardElevation(defaultElevation = 8.dp),
        shape = RoundedCornerShape(24.dp)
    ) {
        Column(modifier = Modifier.padding(18.dp)) {
            content()
        }
    }
}

@Composable
fun BerylMap(modifier: Modifier = Modifier) {

    val context = LocalContext.current

    val mapView = remember {
        MapView(context).apply {
            onCreate(null)
        }
    }

    DisposableEffect(mapView) {
        mapView.onStart()
        mapView.onResume()

        onDispose {
            mapView.onPause()
            mapView.onStop()
            mapView.onDestroy()
        }
    }

    AndroidView(
        modifier = modifier,
        factory = { mapView }
    )

    LaunchedEffect(mapView) {
        mapView.getMapAsync { map ->
            map.setStyle("https://demotiles.maplibre.org/style.json")
        }
    }
}

@Composable
fun BerylCircularHalo(
    modifier: Modifier = Modifier,
    progress: Float,
    strokeWidth: Dp = 6.dp
) {
    Canvas(modifier = modifier) {
        val sweep = 270f * progress
        drawArc(
            color = BerylGreen.copy(alpha = 0.25f),
            startAngle = 135f,
            sweepAngle = 270f,
            useCenter = false,
            style = Stroke(width = strokeWidth.toPx(), cap = StrokeCap.Round)
        )
        drawArc(
            color = BerylGreen,
            startAngle = 135f,
            sweepAngle = sweep,
            useCenter = false,
            style = Stroke(width = strokeWidth.toPx(), cap = StrokeCap.Round)
        )
    }
}

@Composable
fun AnimatedCircleOutline(modifier: Modifier = Modifier) {
    val transition = rememberInfiniteTransition()
    val rotation by transition.animateFloat(
        initialValue = 0f,
        targetValue = 360f,
        animationSpec = infiniteRepeatable(tween(2400, easing = androidx.compose.animation.core.LinearEasing))
    )

    Canvas(modifier = modifier) {
        drawArc(
            color = BerylGreen.copy(alpha = 0.2f),
            startAngle = rotation,
            sweepAngle = 260f,
            useCenter = false,
            style = Stroke(width = 4.dp.toPx(), cap = StrokeCap.Round)
        )
        drawArc(
            color = BerylGreen,
            startAngle = rotation + 40f,
            sweepAngle = 140f,
            useCenter = false,
            style = Stroke(width = 5.dp.toPx(), cap = StrokeCap.Round)
        )
    }
}

@Composable
fun BerylConnectionLink(modifier: Modifier = Modifier) {
    val transition = rememberInfiniteTransition()
    val pulse by transition.animateFloat(
        initialValue = 0.3f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(1800), RepeatMode.Reverse)
    )
    Canvas(modifier = modifier) {
        val start = Offset(0f, size.height / 2f)
        val end = Offset(size.width, size.height / 2f)
        drawLine(
            color = BerylGreen.copy(alpha = 0.5f),
            start = start,
            end = end,
            strokeWidth = 6f,
            cap = StrokeCap.Round
        )
        drawCircle(
            color = BerylGreen.copy(alpha = 0.25f),
            radius = 22f * pulse,
            center = Offset(size.width / 2f, size.height / 2f)
        )
        drawCircle(
            color = BerylGreen,
            radius = 10f,
            center = Offset(size.width / 2f, size.height / 2f)
        )
    }
}

@Composable
fun BerylEnergyLegend() {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(BerylSoft, RoundedCornerShape(16.dp))
            .padding(horizontal = 14.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            modifier = Modifier
                .size(12.dp)
                .clip(CircleShape)
                .background(BerylGreen)
        )
        Spacer(modifier = Modifier.width(8.dp))
        Text(
            text = stringResource(R.string.mobility_energy_legend),
            fontFamily = BerylFontFamily,
            fontSize = 12.sp,
            color = BerylMuted
        )
    }
}

@Composable
fun BerylPill(text: String, modifier: Modifier = Modifier) {
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(50))
            .background(BerylSoft)
            .padding(horizontal = 12.dp, vertical = 6.dp)
    ) {
        Text(text, fontFamily = BerylFontFamily, fontSize = 12.sp, color = BerylMuted)
    }
}

@Composable
fun BerylContractStep(label: String, active: Boolean, modifier: Modifier = Modifier) {
    Row(modifier = modifier, verticalAlignment = Alignment.CenterVertically) {
        Box(
            modifier = Modifier
                .size(10.dp)
                .clip(CircleShape)
                .background(if (active) BerylGreen else BerylMuted.copy(alpha = 0.3f))
        )
        Spacer(modifier = Modifier.width(8.dp))
        Text(
            text = label,
            fontFamily = BerylFontFamily,
            fontSize = 12.sp,
            color = if (active) BerylInk else BerylMuted
        )
    }
}

val BerylFontFamily: FontFamily
    @Composable
    get() = remember {
        FontFamily.SansSerif
    }

@Composable
private fun InfiniteTransition.pulse(min: Float, max: Float) = animateFloat(
    initialValue = min,
    targetValue = max,
    animationSpec = infiniteRepeatable(tween(1400), RepeatMode.Reverse)
)
