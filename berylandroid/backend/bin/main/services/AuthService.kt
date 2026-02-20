class AuthService(private val verifier: TokenVerifier) {
    fun verify(token: String): AuthVerifyResponse {
        val user = verifier.verifyIdToken(token)
        return AuthVerifyResponse(
            uid = user.uid,
            email = user.email,
            name = user.name,
            emailVerified = user.emailVerified
        )
    }
}
