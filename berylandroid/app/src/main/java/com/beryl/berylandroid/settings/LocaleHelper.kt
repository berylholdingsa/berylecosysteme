package com.beryl.berylandroid.settings

import android.content.Context
import android.content.res.Configuration
import android.content.res.Resources
import android.os.Build
import android.os.LocaleList
import java.util.Locale

object LocaleHelper {
    fun wrapContextWithLocale(baseContext: Context, languageTag: String): Context {
        val locale = buildLocale(languageTag)
        Locale.setDefault(locale)
        val configuration = Configuration(baseContext.resources.configuration)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            configuration.setLocales(LocaleList(locale))
        } else {
            configuration.setLocale(locale)
        }
        updateResources(baseContext.resources, configuration)
        return baseContext.createConfigurationContext(configuration)
    }

    fun applyLocale(context: Context, languageTag: String) {
        wrapContextWithLocale(context, languageTag)
    }

    private fun buildLocale(languageTag: String): Locale {
        val cleanedTag = languageTag.takeIf { it.isNotBlank() } ?: LanguageOption.FRENCH.tag
        return Locale.forLanguageTag(cleanedTag)
    }

    private fun updateResources(resources: Resources, configuration: Configuration) {
        resources.updateConfiguration(configuration, resources.displayMetrics)
    }
}
