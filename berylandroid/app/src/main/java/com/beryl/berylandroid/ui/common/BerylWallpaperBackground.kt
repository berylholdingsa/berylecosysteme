package com.beryl.berylandroid.ui.common

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import com.beryl.berylandroid.R

@Composable
fun BerylWallpaperBackground(
    modifier: Modifier = Modifier,
    content: @Composable BoxScope.() -> Unit
) {
    val isDark = isSystemInDarkTheme()

    Box(modifier = modifier.fillMaxSize()) {
        Image(
            painter = painterResource(id = R.drawable.bg_community_light_green),
            contentDescription = null,
            contentScale = ContentScale.Crop,
            alpha = if (isDark) 0.28f else 1f,
            modifier = Modifier.fillMaxSize()
        )
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(
                    if (isDark) {
                        MaterialTheme.colorScheme.background.copy(alpha = 0.72f)
                    } else {
                        MaterialTheme.colorScheme.background.copy(alpha = 0.12f)
                    }
                )
        )
        content()
    }
}
