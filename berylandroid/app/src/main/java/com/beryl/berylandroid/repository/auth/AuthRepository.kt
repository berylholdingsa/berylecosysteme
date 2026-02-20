package com.beryl.berylandroid.repository.auth

import android.app.Activity
import com.beryl.berylandroid.repository.user.UserRepository
import com.beryl.berylandroid.util.awaitResult
import com.google.firebase.auth.AuthCredential
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.auth.FirebaseUser
import com.google.firebase.auth.GoogleAuthProvider
import com.google.firebase.auth.OAuthProvider
import com.google.firebase.auth.PhoneAuthCredential
import com.google.firebase.auth.PhoneAuthOptions
import com.google.firebase.auth.PhoneAuthProvider
import com.google.firebase.auth.UserProfileChangeRequest
import java.util.concurrent.TimeUnit

class AuthRepository(
    private val auth: FirebaseAuth = FirebaseAuth.getInstance(),
    private val userRepository: UserRepository = UserRepository()
) {
    fun currentUser(): FirebaseUser? = auth.currentUser

    fun addAuthStateListener(listener: FirebaseAuth.AuthStateListener) {
        auth.addAuthStateListener(listener)
    }

    fun removeAuthStateListener(listener: FirebaseAuth.AuthStateListener) {
        auth.removeAuthStateListener(listener)
    }

    suspend fun signInWithEmail(email: String, password: String): Result<FirebaseUser> {
        return runCatching {
            val result = auth.signInWithEmailAndPassword(email, password).awaitResult()
            val user = result.user ?: throw IllegalStateException("Utilisateur introuvable")
            userRepository.ensureUserProfile(user)
            user
        }
    }

    suspend fun registerWithEmail(email: String, password: String, displayName: String?): Result<FirebaseUser> {
        return runCatching {
            val result = auth.createUserWithEmailAndPassword(email, password).awaitResult()
            val user = result.user ?: throw IllegalStateException("Utilisateur introuvable")
            if (!displayName.isNullOrBlank()) {
                val request = UserProfileChangeRequest.Builder()
                    .setDisplayName(displayName)
                    .build()
                user.updateProfile(request).awaitResult()
            }
            userRepository.ensureUserProfile(user)
            user
        }
    }

    suspend fun signInWithGoogle(idToken: String): Result<FirebaseUser> {
        return runCatching {
            val credential: AuthCredential = GoogleAuthProvider.getCredential(idToken, null)
            val result = auth.signInWithCredential(credential).awaitResult()
            val user = result.user ?: throw IllegalStateException("Utilisateur introuvable")
            userRepository.ensureUserProfile(user)
            user
        }
    }

    fun startPhoneNumberVerification(
        activity: Activity,
        phoneNumber: String,
        callbacks: PhoneAuthProvider.OnVerificationStateChangedCallbacks,
        forceResendingToken: PhoneAuthProvider.ForceResendingToken? = null
    ) {
        val optionsBuilder = PhoneAuthOptions.newBuilder(auth)
            .setPhoneNumber(phoneNumber)
            .setTimeout(60L, TimeUnit.SECONDS)
            .setActivity(activity)
            .setCallbacks(callbacks)
        if (forceResendingToken != null) {
            optionsBuilder.setForceResendingToken(forceResendingToken)
        }
        PhoneAuthProvider.verifyPhoneNumber(optionsBuilder.build())
    }

    suspend fun signInWithPhoneCredential(credential: PhoneAuthCredential): Result<FirebaseUser> {
        return runCatching {
            val result = auth.signInWithCredential(credential).awaitResult()
            val user = result.user ?: throw IllegalStateException("Utilisateur introuvable")
            userRepository.ensureUserProfile(user)
            user
        }
    }

    suspend fun signInWithApple(activity: Activity): Result<FirebaseUser> {
        return runCatching {
            val pending = auth.pendingAuthResult
            val result = if (pending != null) {
                pending.awaitResult()
            } else {
                val provider = OAuthProvider.newBuilder("apple.com")
                provider.setScopes(listOf("email", "name"))
                auth.startActivityForSignInWithProvider(activity, provider.build()).awaitResult()
            }
            val user = result.user ?: throw IllegalStateException("Utilisateur introuvable")
            userRepository.ensureUserProfile(user)
            user
        }
    }

    fun signOut() {
        auth.signOut()
    }
}
