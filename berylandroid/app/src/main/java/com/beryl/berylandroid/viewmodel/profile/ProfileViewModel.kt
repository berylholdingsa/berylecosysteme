package com.beryl.berylandroid.viewmodel.profile

import android.net.Uri
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.beryl.berylandroid.model.auth.KycDocs
import com.beryl.berylandroid.model.auth.KycStatus
import com.beryl.berylandroid.model.auth.UserProfile
import com.beryl.berylandroid.model.auth.UserRole
import com.beryl.berylandroid.model.kyc.KycDocType
import com.beryl.berylandroid.repository.kyc.KycRepository
import com.beryl.berylandroid.repository.user.UserRepository
import com.beryl.berylandroid.util.ProfileValidation
import com.google.firebase.auth.FirebaseAuth
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

class ProfileViewModel(
    private val auth: FirebaseAuth? = runCatching { FirebaseAuth.getInstance() }.getOrNull(),
    private val userRepository: UserRepository = UserRepository(),
    private val kycRepository: KycRepository = KycRepository()
) : ViewModel() {

    data class ProfileUiState(
        val isLoading: Boolean = true,
        val userProfile: UserProfile? = null,
        val firstName: String = "",
        val lastName: String = "",
        val email: String = "",
        val phoneNumber: String = "",
        val photoUrl: String? = null,
        val kycDocs: KycDocs = KycDocs(),
        val kycStatus: KycStatus = KycStatus.PENDING,
        val kycReason: String? = null,
        val kycVerifiedAt: Long? = null,
        val kycRejectedAt: Long? = null,
        val role: UserRole = UserRole.USER,
        val riskScore: Float = 0f,
        val uploadingDocs: Set<KycDocType> = emptySet(),
        val isSaving: Boolean = false,
        val isSubmitting: Boolean = false,
        val snackbarMessage: String? = null,
        val validationMessage: String? = null
    )

    private val _uiState = MutableStateFlow(ProfileUiState())
    val uiState: StateFlow<ProfileUiState> = _uiState.asStateFlow()

    private val uid = auth?.currentUser?.uid

    init {
        if (uid == null) {
            _uiState.update { it.copy(isLoading = false, snackbarMessage = "Utilisateur non connecté") }
        } else {
            viewModelScope.launch {
                userRepository.observeProfile(uid).collect { profile ->
                    _uiState.update {
                        if (profile == null) {
                            it.copy(isLoading = false)
                        } else {
                            it.copy(
                                isLoading = false,
                                userProfile = profile,
                                firstName = profile.firstName.orEmpty(),
                                lastName = profile.lastName.orEmpty(),
                                email = profile.email.orEmpty(),
                                phoneNumber = profile.phoneNumber.orEmpty(),
                                photoUrl = profile.photoUrl,
                                kycDocs = profile.kycDocs,
                                kycStatus = profile.kycStatus,
                                kycReason = profile.kycReason,
                                kycVerifiedAt = profile.kycVerifiedAt,
                                kycRejectedAt = profile.kycRejectedAt,
                                role = profile.role,
                                riskScore = profile.riskScore
                            )
                        }
                    }
                }
            }
        }
    }

    fun onFirstNameChange(value: String) {
        _uiState.update { it.copy(firstName = value, validationMessage = null) }
    }

    fun onLastNameChange(value: String) {
        _uiState.update { it.copy(lastName = value, validationMessage = null) }
    }

    fun onEmailChange(value: String) {
        _uiState.update { it.copy(email = value, validationMessage = null) }
    }

    fun onPhoneNumberChange(value: String) {
        _uiState.update { it.copy(phoneNumber = value, validationMessage = null) }
    }

    fun saveProfile() {
        val uid = uid ?: return
        val state = _uiState.value
        if (!ProfileValidation.isEmailValid(state.email)) {
            _uiState.update { it.copy(validationMessage = "Email invalide") }
            return
        }
        if (!ProfileValidation.isPhoneValid(state.phoneNumber)) {
            _uiState.update { it.copy(validationMessage = "Téléphone invalide") }
            return
        }
        viewModelScope.launch {
            _uiState.update { it.copy(isSaving = true, validationMessage = null) }
            val updates = mapOf(
                "prenom" to state.firstName.trim(),
                "nom" to state.lastName.trim(),
                "email" to state.email.trim(),
                "phoneNumber" to state.phoneNumber.trim()
            )
            runCatching {
                userRepository.updateProfileFields(uid, updates)
            }.onSuccess {
                _uiState.update {
                    it.copy(isSaving = false, snackbarMessage = "Profil sauvegardé")
                }
            }.onFailure {
                _uiState.update {
                    it.copy(isSaving = false, snackbarMessage = "Impossible de sauvegarder")
                }
            }
        }
    }

    fun uploadDocument(type: KycDocType, uri: Uri) {
        val uid = uid ?: return
        viewModelScope.launch {
            _uiState.update { it.copy(uploadingDocs = it.uploadingDocs + type) }
            val result = kycRepository.uploadDocument(uid, type, uri)
            _uiState.update { it.copy(uploadingDocs = it.uploadingDocs - type) }
            result.fold(
                onSuccess = { url ->
                    userRepository.updateKycDocUrl(uid, type, url)
                    _uiState.update { it.copy(snackbarMessage = "Document enregistré") }
                },
                onFailure = { error ->
                    _uiState.update {
                        it.copy(snackbarMessage = "Téléversement échoué : ${error.message ?: "erreur"}")
                    }
                }
            )
        }
    }

    fun submitKyc() {
        val uid = uid ?: return
        val state = _uiState.value
        if (state.kycStatus == KycStatus.VERIFIED) {
            _uiState.update { it.copy(snackbarMessage = "KYC déjà vérifié") }
            return
        }
        if (!state.kycDocs.completed) {
            _uiState.update { it.copy(snackbarMessage = "Veuillez compléter les trois pièces") }
            return
        }
        viewModelScope.launch {
            _uiState.update { it.copy(isSubmitting = true) }
            runCatching {
                userRepository.updateKycStatus(uid, KycStatus.PENDING)
            }.onSuccess {
                _uiState.update {
                    it.copy(isSubmitting = false, snackbarMessage = "KYC soumis")
                }
            }.onFailure {
                _uiState.update {
                    it.copy(isSubmitting = false, snackbarMessage = "Échec de la soumission")
                }
            }
        }
    }

    fun retryKyc() {
        val uid = uid ?: return
        viewModelScope.launch {
            _uiState.update { it.copy(isSubmitting = true) }
            runCatching {
                userRepository.updateKycStatus(uid, KycStatus.PENDING)
            }.onSuccess {
                _uiState.update {
                    it.copy(isSubmitting = false, snackbarMessage = "Nouvelle tentative enregistrée")
                }
            }.onFailure {
                _uiState.update {
                    it.copy(isSubmitting = false, snackbarMessage = "Impossible de réinitialiser le KYC")
                }
            }
        }
    }

    fun clearSnackbar() {
        _uiState.update { it.copy(snackbarMessage = null) }
    }
}
