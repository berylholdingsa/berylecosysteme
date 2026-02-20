package com.beryl.berylandroid.session

import com.google.android.gms.tasks.Tasks
import com.google.firebase.auth.FirebaseAuth
import java.util.concurrent.TimeUnit

object TokenRefreshManager {
    private const val REFRESH_WINDOW_MS = 2 * 60 * 1000L
    private const val TOKEN_FETCH_TIMEOUT_SECONDS = 8L

    private val lock = Any()

    fun getValidToken(sessionManager: SessionManager = SessionManager): String? {
        val cachedToken = sessionManager.getToken()?.takeIf { it.isNotBlank() }
        val tokenExpiry = sessionManager.getTokenExpiryEpochMillis()
        val shouldRefresh = cachedToken.isNullOrBlank() ||
            tokenExpiry == null ||
            tokenExpiry <= (System.currentTimeMillis() + REFRESH_WINDOW_MS)

        return if (shouldRefresh) {
            refreshToken(forceRefresh = true, sessionManager = sessionManager) ?: cachedToken
        } else {
            cachedToken
        }
    }

    fun refreshToken(
        forceRefresh: Boolean,
        sessionManager: SessionManager = SessionManager
    ): String? {
        synchronized(lock) {
            val currentUser = FirebaseAuth.getInstance().currentUser
                ?: return sessionManager.getToken()
            return try {
                val tokenResult = Tasks.await(
                    currentUser.getIdToken(forceRefresh),
                    TOKEN_FETCH_TIMEOUT_SECONDS,
                    TimeUnit.SECONDS
                )
                val refreshedToken = tokenResult.token?.takeIf { it.isNotBlank() } ?: return null
                sessionManager.updateSession(
                    token = refreshedToken,
                    accountId = sessionManager.getAccountId() ?: currentUser.uid,
                    tokenExpiryEpochMillis = tokenResult.expirationTimestamp
                )
                refreshedToken
            } catch (_: Exception) {
                if (forceRefresh) {
                    null
                } else {
                    sessionManager.getToken()
                }
            }
        }
    }
}
