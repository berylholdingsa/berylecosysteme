import io.ktor.server.routing.Route
import io.ktor.server.routing.get
import io.ktor.server.routing.route
import io.ktor.server.application.call
import io.ktor.server.response.respond

fun Route.userRoutes(userService: UserService) {
    route("/users") {
        get("/me") {
            val authUser = call.attributes[AuthenticatedUserKey]
            val user = userService.getOrCreate(authUser)
            call.respond(user)
        }
    }
}
