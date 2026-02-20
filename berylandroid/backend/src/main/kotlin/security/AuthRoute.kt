import io.ktor.server.application.ApplicationCallPipeline
import io.ktor.server.application.call
import io.ktor.server.request.header
import io.ktor.server.response.respond
import io.ktor.server.routing.Route
import io.ktor.server.routing.RouteSelector
import io.ktor.server.routing.createChild
import io.ktor.http.HttpStatusCode

fun Route.authenticated(verifier: TokenVerifier, block: Route.() -> Unit): Route {
    val child = createChild(object : RouteSelector() {})
    child.intercept(ApplicationCallPipeline.Plugins) {
        val authHeader = call.request.header("Authorization") ?: ""
        val token = authHeader.removePrefix("Bearer ").trim()
        if (token.isBlank()) {
            call.respond(HttpStatusCode.Unauthorized, ErrorResponse("unauthorized", "Missing bearer token"))
            finish()
            return@intercept
        }

        try {
            val user = verifier.verifyIdToken(token)
            call.attributes.put(AuthenticatedUserKey, user)
        } catch (ex: UnauthorizedException) {
            call.respond(HttpStatusCode.Unauthorized, ErrorResponse("unauthorized", ex.message))
            finish()
            return@intercept
        }
    }
    child.block()
    return child
}
