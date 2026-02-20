package com.beryl.esg.ui.components

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.beryl.berylandroid.R
import com.beryl.esg.ui.state.ESGUiState

private val EsgSurfaceShape = RoundedCornerShape(24.dp)
private val EsgButtonColor = Color(0xFF014421)
private val EsgTextPrimary = Color.White
private val EsgTextSecondary = Color.White.copy(alpha = 0.8f)

@Composable
fun ESGPremiumScreen(
    title: String,
    onBack: (() -> Unit)? = null,
    content: @Composable ColumnScope.() -> Unit
) {
    Box(modifier = Modifier.fillMaxSize()) {
        Image(
            painter = painterResource(id = R.drawable.bg_community_light_green),
            contentDescription = null,
            modifier = Modifier.fillMaxSize(),
            contentScale = ContentScale.Crop
        )
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color.White.copy(alpha = 0.05f))
        )

        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp, vertical = 20.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.Start
            ) {
                if (onBack != null) {
                    IconButton(onClick = onBack) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Back",
                            tint = EsgTextPrimary
                        )
                    }
                }
                Text(
                    text = title,
                    color = EsgTextPrimary,
                    fontSize = 22.sp,
                    fontWeight = FontWeight.SemiBold
                )
            }

            content()
            Spacer(modifier = Modifier.height(8.dp))
        }
    }
}

@Composable
fun ESGPremiumCard(
    modifier: Modifier = Modifier,
    content: @Composable ColumnScope.() -> Unit
) {
    Box(
        modifier = modifier
            .fillMaxWidth()
            .shadow(elevation = 8.dp, shape = EsgSurfaceShape)
            .clip(EsgSurfaceShape)
    ) {
        Image(
            painter = painterResource(id = R.drawable.card_berylpay_green_metal),
            contentDescription = null,
            modifier = Modifier.fillMaxSize(),
            contentScale = ContentScale.Crop
        )

        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(24.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            content()
        }
    }
}

@Composable
fun ESGSectionTitle(label: String) {
    Text(
        text = label,
        color = EsgTextPrimary,
        fontSize = 22.sp,
        fontWeight = FontWeight.SemiBold
    )
}

@Composable
fun ESGPrimaryValue(value: String) {
    Text(
        text = value,
        color = EsgTextPrimary,
        fontSize = 32.sp,
        fontWeight = FontWeight.Bold
    )
}

@Composable
fun ESGSecondaryLabel(label: String) {
    Text(
        text = label,
        color = EsgTextSecondary,
        fontSize = 14.sp,
        fontWeight = FontWeight.Medium
    )
}

@Composable
fun ESGPremiumButton(
    text: String,
    onClick: () -> Unit,
    enabled: Boolean = true,
    modifier: Modifier = Modifier
) {
    Button(
        onClick = onClick,
        enabled = enabled,
        modifier = modifier.fillMaxWidth(),
        colors = ButtonDefaults.buttonColors(
            containerColor = EsgButtonColor,
            contentColor = Color.White,
            disabledContainerColor = EsgButtonColor.copy(alpha = 0.4f),
            disabledContentColor = Color.White.copy(alpha = 0.7f)
        ),
        shape = RoundedCornerShape(50)
    ) {
        Text(
            text = text,
            color = Color.White,
            fontWeight = FontWeight.SemiBold,
            modifier = Modifier.padding(horizontal = 12.dp)
        )
    }
}

@Composable
fun <T> ESGStateRenderer(
    state: ESGUiState<T>,
    onRetry: (() -> Unit)? = null,
    content: @Composable (T) -> Unit
) {
    when (state) {
        ESGUiState.Loading -> {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 40.dp),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator(color = Color.White)
            }
        }

        ESGUiState.Empty -> {
            ESGPremiumCard {
                ESGSectionTitle("EMPTY")
                ESGSecondaryLabel("NO_CONTENT")
                if (onRetry != null) {
                    ESGPremiumButton(text = "RETRY", onClick = onRetry)
                }
            }
        }

        is ESGUiState.Error -> {
            ESGPremiumCard {
                ESGSectionTitle("ERROR")
                ESGPrimaryValue(state.code)
                ESGSecondaryLabel("ERROR_CODE")
                if (onRetry != null) {
                    ESGPremiumButton(text = "RETRY", onClick = onRetry)
                }
            }
        }

        is ESGUiState.Content -> {
            content(state.data)
        }
    }
}

@Composable
fun ESGBooleanValue(value: Boolean) {
    val label = if (value) "TRUE" else "FALSE"
    val color = if (value) Color(0xFFB9F6CA) else Color(0xFFFFCDD2)
    Text(
        text = label,
        style = MaterialTheme.typography.titleMedium,
        color = color,
        textAlign = TextAlign.Start,
        fontWeight = FontWeight.Bold
    )
}

fun formatDecimal(value: Double): String = String.format("%.3f", value)
