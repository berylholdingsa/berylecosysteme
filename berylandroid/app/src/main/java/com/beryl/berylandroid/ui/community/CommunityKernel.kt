package com.beryl.berylandroid.ui.community

object CommunityKernel {
    val permissionManager: PermissionManager by lazy { PermissionManager() }
    val contactManager: ContactManager by lazy { ContactManager(permissionManager) }
}
