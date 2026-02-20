package com.beryl.berylandroid.ui.community.chat

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
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
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.Card
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.produceState
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.navigation.NavHostController
import com.beryl.berylandroid.R
import com.beryl.berylandroid.ui.community.CommunityDestination
import com.beryl.berylandroid.ui.community.CommunityKernel
import com.beryl.berylandroid.ui.community.safeNavigate
import com.beryl.berylandroid.ui.theme.premiumCardBorder
import com.beryl.berylandroid.ui.theme.premiumCardColors
import com.beryl.berylandroid.viewmodel.community.CommunityViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun NewChatScreen(navController: NavHostController, viewModel: CommunityViewModel) {
    val context = LocalContext.current
    val permissionManager = remember { CommunityKernel.permissionManager }
    val contactManager = remember { CommunityKernel.contactManager }
    val permission = remember { permissionManager.readContactsPermission() }

    var search by rememberSaveable { mutableStateOf("") }
    var hasRequestedPermission by rememberSaveable { mutableStateOf(false) }
    var hasReadContactsPermission by remember {
        mutableStateOf(permissionManager.hasReadContactsPermission(context))
    }

    val permissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { granted ->
        hasReadContactsPermission = granted
    }

    LaunchedEffect(context) {
        hasReadContactsPermission = permissionManager.hasReadContactsPermission(context)
    }

    val allContacts by produceState(
        initialValue = emptyList<String>(),
        key1 = hasReadContactsPermission
    ) {
        value = if (hasReadContactsPermission) {
            withContext(Dispatchers.IO) {
                contactManager.loadContactDisplayNames(context)
            }
        } else {
            emptyList()
        }
    }

    val contacts = remember(allContacts, search) {
        allContacts.filter { it.contains(search, ignoreCase = true) }
    }

    val isDark = isSystemInDarkTheme()

    LaunchedEffect(hasReadContactsPermission, hasRequestedPermission) {
        if (!hasReadContactsPermission && !hasRequestedPermission) {
            hasRequestedPermission = true
            permissionLauncher.launch(permission)
        }
    }

    val openConversation: (String) -> Unit = { contact ->
        val id = viewModel.createConversation(contact)
        navController.safeNavigate(CommunityDestination.ChatDetail.createRoute(id)) {
            launchSingleTop = true
            popUpTo(CommunityDestination.ChatHome.route) { inclusive = false }
        }
    }

    Column(modifier = Modifier.fillMaxSize(), horizontalAlignment = Alignment.CenterHorizontally) {
        TopAppBar(
            title = {
                Text(
                    stringResource(R.string.new_chat_title),
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.onBackground
                )
            },
            colors = TopAppBarDefaults.topAppBarColors(
                containerColor = MaterialTheme.colorScheme.surface.copy(alpha = if (isDark) 0.92f else 0.78f)
            )
        )
        if (hasReadContactsPermission) {
            OutlinedTextField(
                value = search,
                onValueChange = { search = it },
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                placeholder = { Text(stringResource(R.string.new_chat_search_placeholder)) },
                leadingIcon = {
                    Icon(
                        Icons.Default.Search,
                        contentDescription = stringResource(R.string.new_chat_search_content_description)
                    )
                },
                shape = CircleShape
            )

            if (contacts.isEmpty()) {
                EmptyContactsState(hasSearchTerm = search.isNotBlank())
            } else {
                LazyColumn(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(horizontal = 16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    items(contacts, key = { it }) { contact ->
                        Card(
                            modifier = Modifier
                                .fillMaxWidth()
                                .shadow(if (isDark) 12.dp else 6.dp, shape = RoundedCornerShape(20.dp))
                                .clickable { openConversation(contact) },
                            shape = RoundedCornerShape(20.dp),
                            colors = premiumCardColors(),
                            border = premiumCardBorder()
                        ) {
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(16.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(
                                    text = contact,
                                    fontWeight = FontWeight.SemiBold,
                                    color = MaterialTheme.colorScheme.onBackground
                                )
                                Spacer(modifier = Modifier.weight(1f))
                                TextButton(onClick = { openConversation(contact) }) {
                                    Text(
                                        stringResource(R.string.new_chat_start_action),
                                        color = MaterialTheme.colorScheme.onBackground
                                    )
                                }
                            }
                        }
                    }
                }
            }
        } else {
            PermissionStateCard(
                showRationale = permissionManager.shouldShowReadContactsRationale(context),
                onRequestPermission = {
                    hasRequestedPermission = true
                    permissionLauncher.launch(permission)
                }
            )
        }
    }
}

@Composable
private fun PermissionStateCard(
    showRationale: Boolean,
    onRequestPermission: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = if (showRationale) {
                "Beryl Community a besoin de l'autorisation Contacts pour démarrer des discussions réelles."
            } else {
                "Autorisez l'accès aux contacts pour voir vos contacts réels."
            },
            color = MaterialTheme.colorScheme.onBackground
        )
        Spacer(modifier = Modifier.height(8.dp))
        TextButton(onClick = onRequestPermission) {
            Text(text = "Autoriser")
        }
    }
}

@Composable
private fun EmptyContactsState(hasSearchTerm: Boolean) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = if (hasSearchTerm) {
                "Aucun contact ne correspond à cette recherche."
            } else {
                "Aucun contact disponible sur cet appareil."
            },
            color = MaterialTheme.colorScheme.onBackground
        )
    }
}
