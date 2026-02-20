package com.beryl.berylandroid

import android.app.Application
import com.beryl.berylandroid.security.DeviceSecurityManager
import com.beryl.berylandroid.session.SessionManager
import com.mapbox.mapboxsdk.Mapbox

class BerylApplication : Application() {

    override fun onCreate() {
        super.onCreate()
        SessionManager.initialize(this)
        DeviceSecurityManager.initialize(this)
        Mapbox.getInstance(this)
    }
}
