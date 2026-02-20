package com.beryl.berylandroid.ui.community

import android.Manifest
import android.app.Activity
import android.content.Context
import android.content.ContextWrapper
import android.content.pm.PackageManager
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat

class PermissionManager {
    fun readContactsPermission(): String = Manifest.permission.READ_CONTACTS

    fun hasReadContactsPermission(context: Context): Boolean {
        return ContextCompat.checkSelfPermission(
            context,
            readContactsPermission()
        ) == PackageManager.PERMISSION_GRANTED
    }

    fun shouldShowReadContactsRationale(context: Context): Boolean {
        val activity = context.findActivity() ?: return false
        return ActivityCompat.shouldShowRequestPermissionRationale(
            activity,
            readContactsPermission()
        )
    }

    private tailrec fun Context.findActivity(): Activity? {
        return when (this) {
            is Activity -> this
            is ContextWrapper -> baseContext.findActivity()
            else -> null
        }
    }
}
