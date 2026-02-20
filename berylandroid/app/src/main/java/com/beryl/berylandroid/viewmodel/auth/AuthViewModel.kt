package com.beryl.berylandroid.viewmodel.auth

import android.app.Activity
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.beryl.berylandroid.repository.auth.AuthRepository
import com.beryl.berylandroid.session.SessionManager
import com.beryl.berylandroid.util.awaitResult
import com.google.firebase.FirebaseException
import com.google.firebase.auth.FirebaseUser
import com.google.firebase.auth.PhoneAuthCredential
import com.google.firebase.auth.PhoneAuthProvider
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class AuthViewModel(
    private val authRepository: AuthRepository = AuthRepository()
) : ViewModel() {

    sealed class AuthState {
        object Loading : AuthState()
        object Unauthenticated : AuthState()
        data class Authenticated(val user: AuthUser) : AuthState()
    }

    data class AuthUser(
        val uid: String,
        val displayName: String?,
        val email: String?,
        val photoUrl: String?
    )

    private val _authState = MutableStateFlow<AuthState>(AuthState.Unauthenticated)
    val authState: StateFlow<AuthState> = _authState.asStateFlow()

    private val _errorMessage = MutableStateFlow<String?>(null)
    val errorMessage: StateFlow<String?> = _errorMessage.asStateFlow()

    private var lastPhoneNumber: String? = null
    private var phoneVerificationId: String? = null
    private var phoneResendToken: PhoneAuthProvider.ForceResendingToken? = null

    init {
        _authState.value = AuthState.Unauthenticated
    }

    override fun onCleared() {
        super.onCleared()
    }

    fun signInWithEmail(email: String, password: String) {
        viewModelScope.launch {
            _errorMessage.value = null
            authRepository.signInWithEmail(email, password)
                .onSuccess { setAuthenticated(it) }
                .onFailure { _errorMessage.value = it.localizedMessage }
        }
    }

    fun registerWithEmail(email: String, password: String, displayName: String?) {
        viewModelScope.launch {
            _errorMessage.value = null
            authRepository.registerWithEmail(email, password, displayName)
                .onSuccess { setAuthenticated(it) }
                .onFailure { _errorMessage.value = it.localizedMessage }
        }
    }

    fun signInWithGoogle(idToken: String) {
        viewModelScope.launch {
            _errorMessage.value = null
            authRepository.signInWithGoogle(idToken)
                .onSuccess { setAuthenticated(it) }
                .onFailure { _errorMessage.value = it.localizedMessage }
        }
    }

    fun signInWithApple(activity: Activity) {
        viewModelScope.launch {
            _errorMessage.value = null
            authRepository.signInWithApple(activity)
                .onSuccess { setAuthenticated(it) }
                .onFailure { _errorMessage.value = it.localizedMessage }
        }
    }

    fun signInWithPhone(activity: Activity, phoneNumber: String, smsCode: String) {
        viewModelScope.launch {
            _errorMessage.value = null
            if (lastPhoneNumber != phoneNumber) {
                lastPhoneNumber = phoneNumber
                phoneVerificationId = null
                phoneResendToken = null
            }
            if (smsCode.isBlank() || phoneVerificationId == null) {
                requestPhoneVerification(activity, phoneNumber)
            } else {
                verifyPhoneCode(smsCode)
            }
        }
    }

    fun signOut() {
        SessionManager.clearSession()
        authRepository.signOut()
        setUnauthenticated()
    }

    fun reportError(message: String) {
        _errorMessage.value = message
    }

    private fun requestPhoneVerification(activity: Activity, phoneNumber: String) {
        authRepository.startPhoneNumberVerification(
            activity = activity,
            phoneNumber = phoneNumber,
            callbacks = object : PhoneAuthProvider.OnVerificationStateChangedCallbacks() {
                override fun onVerificationCompleted(credential: PhoneAuthCredential) {
                    viewModelScope.launch {
                        authRepository.signInWithPhoneCredential(credential)
                            .onSuccess { setAuthenticated(it) }
                            .onFailure { _errorMessage.value = it.localizedMessage }
                    }
                }

                override fun onVerificationFailed(exception: FirebaseException) {
                    _errorMessage.value = exception.localizedMessage
                }

                override fun onCodeSent(
                    verificationId: String,
                    token: PhoneAuthProvider.ForceResendingToken
                ) {
                    phoneVerificationId = verificationId
                    phoneResendToken = token
                    _errorMessage.value =
                        "Code envoyé par SMS. Saisissez-le puis reconnectez-vous."
                }
            },
            forceResendingToken = phoneResendToken
        )
    }

    private fun verifyPhoneCode(code: String) {
        val verificationId = phoneVerificationId ?: return
        val credential = PhoneAuthProvider.getCredential(verificationId, code)
        viewModelScope.launch {
            authRepository.signInWithPhoneCredential(credential)
                .onSuccess { setAuthenticated(it) }
                .onFailure { _errorMessage.value = it.localizedMessage }
        }
    }

    private fun setAuthenticated(user: FirebaseUser) {
        lastPhoneNumber = null
        phoneVerificationId = null
        phoneResendToken = null
        SessionManager.updateSession(token = null, accountId = user.uid)
        viewModelScope.launch {
            val tokenResult = runCatching {
                user.getIdToken(false).awaitResult()
            }.getOrNull()
            SessionManager.updateSession(
                token = tokenResult?.token,
                accountId = user.uid,
                tokenExpiryEpochMillis = tokenResult?.expirationTimestamp
            )
        }
        _authState.value = AuthState.Authenticated(
            AuthUser(
                uid = user.uid,
                displayName = user.displayName,
                email = user.email,
                photoUrl = user.photoUrl?.toString()
            )
        )
    }

    private fun setUnauthenticated() {
        lastPhoneNumber = null
        phoneVerificationId = null
        phoneResendToken = null
        _authState.value = AuthState.Unauthenticated
    }
}
