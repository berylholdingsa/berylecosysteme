package com.beryl.berylandroid.settings

import android.content.Context
import android.content.res.Configuration
import android.os.LocaleList
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalContext
import java.util.Locale

@Composable
fun ProvideAppLocale(
    languageTag: String,
    content: @Composable () -> Unit
) {
    val baseContext = LocalContext.current
    val localizedConfig = remember(baseContext, languageTag) {
        val locale = Locale.forLanguageTag(languageTag)
        Configuration(baseContext.resources.configuration).apply {
            setLocales(LocaleList(locale))
        }
    }
    val localizedContext = remember(baseContext, languageTag) {
        baseContext.createConfigurationContext(localizedConfig)
    }
    CompositionLocalProvider(
        LocalContext provides localizedContext,
        LocalConfiguration provides localizedConfig
    ) {
        content()
    }
}
