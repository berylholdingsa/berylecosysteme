package com.beryl.berylandroid.ui.community

import android.content.Context
import android.provider.ContactsContract

class ContactManager(
    private val permissionManager: PermissionManager = PermissionManager()
) {
    fun loadContactDisplayNames(context: Context): List<String> {
        if (!permissionManager.hasReadContactsPermission(context)) return emptyList()

        val names = linkedSetOf<String>()
        val projection = arrayOf(ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME_PRIMARY)

        context.contentResolver.query(
            ContactsContract.CommonDataKinds.Phone.CONTENT_URI,
            projection,
            null,
            null,
            "${ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME_PRIMARY} ASC"
        )?.use { cursor ->
            val nameColumn = cursor.getColumnIndex(ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME_PRIMARY)
            if (nameColumn == -1) return emptyList()

            while (cursor.moveToNext()) {
                val name = cursor.getString(nameColumn)?.trim().orEmpty()
                if (name.isNotEmpty()) names += name
            }
        }

        return names.toList()
    }
}
