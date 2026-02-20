package com.beryl.berylandroid.settings

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.beryl.berylandroid.R
import com.beryl.berylandroid.ui.theme.BerylDarkText
import com.beryl.berylandroid.ui.theme.BerylGreen
import com.beryl.berylandroid.ui.theme.premiumCardBorder
import com.beryl.berylandroid.ui.theme.premiumCardColors

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    onBack: () -> Unit,
    viewModel: SettingsViewModel = viewModel(
        factory = SettingsViewModelFactory(LocalContext.current)
    )
) {
    val settings by viewModel.settings.collectAsState()
    val isDark = isSystemInDarkTheme()
    val textColor = if (isDark) Color.White else Color.Unspecified
    val titleColor = if (isDark) BerylDarkText else BerylGreen

    Scaffold(
        containerColor = Color.Transparent,
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = stringResource(R.string.settings_title),
                        color = textColor,
                        fontWeight = FontWeight.SemiBold
                    )
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(
                            imageVector = Icons.Filled.ArrowBack,
                            contentDescription = stringResource(R.string.settings_back),
                            tint = titleColor
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.surface)
            )
        }
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .background(Color.Transparent)
                .padding(innerPadding)
                .padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(20.dp)
        ) {
            SettingsSection(
                title = stringResource(R.string.settings_theme),
                textColor = textColor
            ) {
                ThemeOptionRow(
                    label = stringResource(R.string.theme_system),
                    selected = settings.theme == ThemeOption.SYSTEM,
                    textColor = textColor,
                    onSelect = { viewModel.setTheme(ThemeOption.SYSTEM) }
                )
                ThemeOptionRow(
                    label = stringResource(R.string.theme_light),
                    selected = settings.theme == ThemeOption.LIGHT,
                    textColor = textColor,
                    onSelect = { viewModel.setTheme(ThemeOption.LIGHT) }
                )
                ThemeOptionRow(
                    label = stringResource(R.string.theme_dark),
                    selected = settings.theme == ThemeOption.DARK,
                    textColor = textColor,
                    onSelect = { viewModel.setTheme(ThemeOption.DARK) }
                )
            }

            SettingsSection(
                title = stringResource(R.string.settings_language),
                textColor = textColor
            ) {
                ThemeOptionRow(
                    label = stringResource(R.string.language_french),
                    selected = settings.language == LanguageOption.FRENCH,
                    textColor = textColor,
                    onSelect = { viewModel.setLanguage(LanguageOption.FRENCH) }
                )
                ThemeOptionRow(
                    label = stringResource(R.string.language_english),
                    selected = settings.language == LanguageOption.ENGLISH,
                    textColor = textColor,
                    onSelect = { viewModel.setLanguage(LanguageOption.ENGLISH) }
                )
            }
        }
    }
}

@Composable
private fun SettingsSection(
    title: String,
    textColor: Color,
    content: @Composable () -> Unit
) {
    val isDark = isSystemInDarkTheme()
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = premiumCardColors(),
        elevation = CardDefaults.cardElevation(defaultElevation = if (isDark) 8.dp else 1.dp),
        border = premiumCardBorder()
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text(
                text = title,
                style = MaterialTheme.typography.titleMedium,
                color = textColor
            )
            content()
        }
    }
}

@Composable
private fun ThemeOptionRow(
    label: String,
    selected: Boolean,
    textColor: Color,
    onSelect: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onSelect)
            .padding(vertical = 6.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        RadioButton(selected = selected, onClick = onSelect)
        Text(
            text = label,
            color = textColor,
            modifier = Modifier.padding(start = 8.dp)
        )
    }
}
