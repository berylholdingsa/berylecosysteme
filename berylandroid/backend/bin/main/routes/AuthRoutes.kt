import io.ktor.server.routing.Route
import io.ktor.server.routing.post
import io.ktor.server.routing.route
import io.ktor.server.application.call
import io.ktor.server.request.receive
import io.ktor.server.response.respond

fun Route.authRoutes(authService: AuthService) {
    route("/auth") {
        post("/verify") {
            val request = call.receive<AuthVerifyRequest>()
            val response = authService.verify(request.idToken)
            call.respond(response)
        }
    }
}
