package com.beryl.berylandroid.ui.theme

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.border
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.unit.dp

@Composable
fun premiumButtonModifier(
    base: Modifier = Modifier,
    shape: Shape = MaterialTheme.shapes.medium
): Modifier {
    val isDark = isSystemInDarkTheme()
    return if (isDark) {
        base
            .shadow(10.dp, shape, clip = false)
            .border(BorderStroke(1.dp, BerylGreen.copy(alpha = 0.6f)), shape)
    } else {
        base
    }
}

@Composable
fun premiumButtonColors() = ButtonDefaults.buttonColors(
    containerColor = BerylGreen,
    contentColor = Color.White
)

@Composable
fun premiumCardColors() = CardDefaults.cardColors(
    containerColor = if (isSystemInDarkTheme()) BerylDarkSurface else MaterialTheme.colorScheme.surface
)

@Composable
fun premiumCardBorder(): BorderStroke? {
    return if (isSystemInDarkTheme()) BorderStroke(1.dp, BerylDarkBorder) else null
}
