package com.beryl.berylandroid.settings

enum class ThemeOption {
    SYSTEM,
    LIGHT,
    DARK
}

enum class LanguageOption(val tag: String) {
    FRENCH("fr"),
    ENGLISH("en")
}

data class AppSettings(
    val theme: ThemeOption = ThemeOption.SYSTEM,
    val language: LanguageOption = LanguageOption.FRENCH
)
