package com.beryl.berylandroid.settings

import android.content.Context
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.settingsDataStore by preferencesDataStore(name = "user_settings")

class SettingsRepository(private val context: Context) {
    private val themeKey = stringPreferencesKey("theme_option")
    private val languageKey = stringPreferencesKey("language_option")

    val settingsFlow: Flow<AppSettings> = context.settingsDataStore.data.map { prefs ->
        AppSettings(
            theme = prefs.parseTheme(),
            language = prefs.parseLanguage()
        )
    }

    suspend fun setTheme(option: ThemeOption) {
        context.settingsDataStore.edit { prefs ->
            prefs[themeKey] = option.name
        }
    }

    suspend fun setLanguage(option: LanguageOption) {
        context.settingsDataStore.edit { prefs ->
            prefs[languageKey] = option.name
        }
    }

    private fun Preferences.parseTheme(): ThemeOption {
        val value = get(themeKey) ?: ThemeOption.SYSTEM.name
        return runCatching { ThemeOption.valueOf(value) }.getOrDefault(ThemeOption.SYSTEM)
    }

    private fun Preferences.parseLanguage(): LanguageOption {
        val value = get(languageKey) ?: LanguageOption.FRENCH.name
        return runCatching { LanguageOption.valueOf(value) }.getOrDefault(LanguageOption.FRENCH)
    }
}
