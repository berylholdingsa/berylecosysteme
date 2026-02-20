package com.beryl.berylandroid.screens

import androidx.compose.runtime.Composable
import com.beryl.sentinel.sdk.SentinelClient

@Composable
fun HomeScreen(
    sentinelClient: SentinelClient,
    onSignOut: () -> Unit
) {
    BerylCommunityScreen(sentinelClient = sentinelClient, onSignOut = onSignOut)
}
