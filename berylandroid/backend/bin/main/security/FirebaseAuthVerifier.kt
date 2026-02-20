import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.auth.FirebaseAuthException

interface TokenVerifier {
    fun verifyIdToken(token: String): AuthenticatedUser
}

class FirebaseAuthVerifier(private val firebaseAuth: FirebaseAuth) : TokenVerifier {
    override fun verifyIdToken(token: String): AuthenticatedUser {
        try {
            val decoded = firebaseAuth.verifyIdToken(token)
            return AuthenticatedUser(
                uid = decoded.uid,
                email = decoded.email,
                name = decoded.name,
                emailVerified = decoded.isEmailVerified
            )
        } catch (ex: FirebaseAuthException) {
            throw UnauthorizedException("Invalid Firebase token")
        } catch (ex: Exception) {
            throw UnauthorizedException("Invalid Firebase token")
        }
    }
}
