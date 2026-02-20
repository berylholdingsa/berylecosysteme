package com.beryl.berylandroid.security

import android.content.Context
import android.os.Build
import com.beryl.berylandroid.BuildConfig
import java.io.File
import java.security.MessageDigest

object DeviceSecurityManager {
    private val lock = Any()

    @Volatile
    private var appContext: Context? = null

    @Volatile
    private var cachedRootStatus: Boolean? = null

    fun initialize(context: Context) {
        appContext = context.applicationContext
    }

    fun shouldBlockForRootRisk(): Boolean {
        return !BuildConfig.DEBUG && isRooted()
    }

    fun isRooted(): Boolean {
        cachedRootStatus?.let { return it }
        synchronized(lock) {
            cachedRootStatus?.let { return it }
            val rooted = hasTestKeys() || hasSuBinary() || canRunSuCommand()
            cachedRootStatus = rooted
            return rooted
        }
    }

    fun getFingerprint(): String {
        val context = appContext
        val rawValue = listOf(
            context?.packageName.orEmpty(),
            Build.BRAND.orEmpty(),
            Build.MODEL.orEmpty(),
            Build.DEVICE.orEmpty(),
            Build.VERSION.SDK_INT.toString(),
            Build.SUPPORTED_ABIS.firstOrNull().orEmpty()
        ).joinToString("|")
        return sha256(rawValue).take(32)
    }

    private fun hasTestKeys(): Boolean {
        return Build.TAGS?.contains("test-keys") == true
    }

    private fun hasSuBinary(): Boolean {
        val paths = arrayOf(
            "/system/app/Superuser.apk",
            "/sbin/su",
            "/system/bin/su",
            "/system/xbin/su",
            "/data/local/xbin/su",
            "/data/local/bin/su",
            "/system/sd/xbin/su",
            "/system/bin/failsafe/su",
            "/data/local/su"
        )
        return paths.any { File(it).exists() }
    }

    private fun canRunSuCommand(): Boolean {
        return runCatching {
            val process = Runtime.getRuntime().exec(arrayOf("/system/xbin/which", "su"))
            process.inputStream.bufferedReader().use { reader ->
                reader.readLine() != null
            }
        }.getOrDefault(false)
    }

    private fun sha256(input: String): String {
        val digest = MessageDigest.getInstance("SHA-256").digest(input.toByteArray())
        val builder = StringBuilder(digest.size * 2)
        for (byte in digest) {
            builder.append(String.format("%02x", byte))
        }
        return builder.toString()
    }
}
