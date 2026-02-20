package com.beryl.berylandroid.viewmodel.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.beryl.berylandroid.model.auth.UserProfile
import com.beryl.berylandroid.repository.user.UserRepository
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.auth.FirebaseUser
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.launch

class UserViewModel(
    private val userRepository: UserRepository = UserRepository(),
    private val auth: FirebaseAuth = FirebaseAuth.getInstance()
) : ViewModel() {

    private val _currentUserProfile = MutableStateFlow<UserProfile?>(null)
    val currentUserProfile: StateFlow<UserProfile?> = _currentUserProfile.asStateFlow()

    private var profileJob: Job? = null

    private val authStateListener = FirebaseAuth.AuthStateListener { firebase ->
        viewModelScope.launch {
            handleAuthenticatedUser(firebase.currentUser)
        }
    }

    init {
        auth.addAuthStateListener(authStateListener)
        viewModelScope.launch {
            handleAuthenticatedUser(auth.currentUser)
        }
    }

    private suspend fun handleAuthenticatedUser(user: FirebaseUser?) {
        profileJob?.cancel()
        if (user == null) {
            _currentUserProfile.value = null
            return
        }
        profileJob = viewModelScope.launch {
            userRepository.observeProfile(user.uid).collect { profile ->
                _currentUserProfile.value = profile
            }
        }
    }

    override fun onCleared() {
        super.onCleared()
        profileJob?.cancel()
        auth.removeAuthStateListener(authStateListener)
    }
}
