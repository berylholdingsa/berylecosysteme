package com.beryl.berylandroid.session

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import java.util.UUID

object SessionManager {
    private const val LEGACY_PREFS_NAME = "beryl_session"
    private const val ENCRYPTED_PREFS_NAME = "beryl_session_encrypted"
    private const val KEY_TOKEN = "token"
    private const val KEY_TOKEN_EXPIRY_EPOCH_MS = "token_expiry_epoch_ms"
    private const val KEY_ACCOUNT_ID = "account_id"
    private const val KEY_CORRELATION_ID = "correlation_id"
    private const val KEY_MIGRATION_DONE = "_migrated_to_encrypted_v1"

    private val lock = Any()

    @Volatile
    private var appContext: Context? = null

    @Volatile
    private var cachedPreferences: SharedPreferences? = null

    fun initialize(context: Context) {
        appContext = context.applicationContext
        preferences()
    }

    fun updateSession(
        token: String?,
        accountId: String?,
        tokenExpiryEpochMillis: Long? = null
    ) {
        val prefs = preferences() ?: return
        val previousAccountId = prefs.getString(KEY_ACCOUNT_ID, null)
        prefs.edit()
            .apply {
                if (token.isNullOrBlank()) {
                    remove(KEY_TOKEN)
                    remove(KEY_TOKEN_EXPIRY_EPOCH_MS)
                } else {
                    putString(KEY_TOKEN, token)
                    if (tokenExpiryEpochMillis == null) {
                        remove(KEY_TOKEN_EXPIRY_EPOCH_MS)
                    } else {
                        putLong(KEY_TOKEN_EXPIRY_EPOCH_MS, tokenExpiryEpochMillis)
                    }
                }
                if (accountId.isNullOrBlank()) {
                    remove(KEY_ACCOUNT_ID)
                } else {
                    putString(KEY_ACCOUNT_ID, accountId)
                }
                if (!accountId.isNullOrBlank() && previousAccountId != null && previousAccountId != accountId) {
                    remove(KEY_CORRELATION_ID)
                }
            }
            .apply()
    }

    fun getToken(): String? {
        return preferences()?.getString(KEY_TOKEN, null)?.takeIf { it.isNotBlank() }
    }

    fun getAccountId(): String? {
        return preferences()?.getString(KEY_ACCOUNT_ID, null)?.takeIf { it.isNotBlank() }
    }

    fun getTokenExpiryEpochMillis(): Long? {
        val prefs = preferences() ?: return null
        if (!prefs.contains(KEY_TOKEN_EXPIRY_EPOCH_MS)) {
            return null
        }
        val value = prefs.getLong(KEY_TOKEN_EXPIRY_EPOCH_MS, 0L)
        return value.takeIf { it > 0L }
    }

    fun getOrCreateCorrelationId(): String {
        val prefs = preferences()
            ?: return UUID.randomUUID().toString()
        val existing = prefs.getString(KEY_CORRELATION_ID, null)?.trim()
        if (!existing.isNullOrEmpty()) {
            return existing
        }
        val generated = UUID.randomUUID().toString()
        prefs.edit().putString(KEY_CORRELATION_ID, generated).apply()
        return generated
    }

    fun clearSession() {
        preferences()?.edit()?.clear()?.apply()
    }

    private fun preferences(): SharedPreferences? {
        cachedPreferences?.let { return it }
        val context = appContext ?: return null
        synchronized(lock) {
            cachedPreferences?.let { return it }
            val (preferences, encrypted) = buildPreferences(context)
            if (encrypted) {
                migrateLegacyIfNeeded(context, preferences)
            }
            cachedPreferences = preferences
            return preferences
        }
    }

    private fun buildPreferences(context: Context): Pair<SharedPreferences, Boolean> {
        return try {
            val masterKey = MasterKey.Builder(context)
                .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
                .build()
            val encryptedPreferences = EncryptedSharedPreferences.create(
                context,
                ENCRYPTED_PREFS_NAME,
                masterKey,
                EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
                EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
            )
            encryptedPreferences to true
        } catch (_: Exception) {
            context.getSharedPreferences(LEGACY_PREFS_NAME, Context.MODE_PRIVATE) to false
        }
    }

    private fun migrateLegacyIfNeeded(
        context: Context,
        encryptedPreferences: SharedPreferences
    ) {
        if (encryptedPreferences.getBoolean(KEY_MIGRATION_DONE, false)) {
            return
        }
        val legacyPreferences = context.getSharedPreferences(LEGACY_PREFS_NAME, Context.MODE_PRIVATE)
        if (legacyPreferences.all.isNotEmpty()) {
            val legacyToken = legacyPreferences.getString(KEY_TOKEN, null)
            val legacyAccountId = legacyPreferences.getString(KEY_ACCOUNT_ID, null)
            encryptedPreferences.edit()
                .apply {
                    if (!legacyToken.isNullOrBlank()) {
                        putString(KEY_TOKEN, legacyToken)
                    }
                    if (!legacyAccountId.isNullOrBlank()) {
                        putString(KEY_ACCOUNT_ID, legacyAccountId)
                    }
                    putBoolean(KEY_MIGRATION_DONE, true)
                }
                .apply()
            legacyPreferences.edit().clear().apply()
        } else {
            encryptedPreferences.edit().putBoolean(KEY_MIGRATION_DONE, true).apply()
        }
    }
}
