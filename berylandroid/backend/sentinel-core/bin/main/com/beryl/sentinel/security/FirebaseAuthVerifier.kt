package com.beryl.sentinel.security

import com.google.auth.oauth2.GoogleCredentials
import com.google.firebase.FirebaseApp
import com.google.firebase.FirebaseOptions
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.auth.FirebaseToken

interface JwtVerifier {
    fun verifyIdToken(token: String, checkRevoked: Boolean = true): AuthenticatedPrincipal
}

class FirebaseAuthVerifier private constructor(
    private val firebaseAuth: FirebaseAuth,
    private val projectId: String
) : JwtVerifier {

    override fun verifyIdToken(token: String, checkRevoked: Boolean): AuthenticatedPrincipal {
        val cleaned = token.trim()
        if (cleaned.isEmpty()) {
            throw UnauthorizedException("Missing bearer token.")
        }
        val decodedToken = runCatching {
            firebaseAuth.verifyIdToken(cleaned, checkRevoked)
        }.getOrElse {
            throw UnauthorizedException("Firebase token verification failed.")
        }
        validateTokenClaims(decodedToken)
        return AuthenticatedPrincipal(
            uid = decodedToken.uid,
            claims = decodedToken.claims
        )
    }

    private fun validateTokenClaims(token: FirebaseToken) {
        if (token.uid.isBlank()) {
            throw UnauthorizedException("Token uid is missing.")
        }
        val expectedIssuer = "https://securetoken.google.com/$projectId"
        if (token.issuer != expectedIssuer) {
            throw UnauthorizedException("Token issuer is invalid.")
        }
        val audience = token.claims["aud"]?.toString()
        if (audience != projectId) {
            throw UnauthorizedException("Token audience is invalid.")
        }
    }

    companion object {
        fun fromEnvironment(): FirebaseAuthVerifier {
            val projectId = resolveProjectId()
                ?: throw IllegalStateException("FIREBASE_PROJECT_ID must be provided for JWT verification.")
            val app = if (FirebaseApp.getApps().isEmpty()) {
                val options = FirebaseOptions.builder()
                    .setCredentials(GoogleCredentials.getApplicationDefault())
                    .setProjectId(projectId)
                    .build()
                FirebaseApp.initializeApp(options)
            } else {
                FirebaseApp.getInstance()
            }
            return FirebaseAuthVerifier(
                firebaseAuth = FirebaseAuth.getInstance(app),
                projectId = projectId
            )
        }

        private fun resolveProjectId(): String? {
            return System.getenv("FIREBASE_PROJECT_ID")
                ?.takeIf { it.isNotBlank() }
                ?: System.getProperty("FIREBASE_PROJECT_ID")
                    ?.takeIf { it.isNotBlank() }
        }
    }
}
