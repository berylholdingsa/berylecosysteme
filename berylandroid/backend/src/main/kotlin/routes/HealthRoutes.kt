import io.ktor.server.routing.Route
import io.ktor.server.routing.get
import io.ktor.server.routing.route
import io.ktor.server.application.call
import io.ktor.server.response.respond
import io.ktor.http.HttpStatusCode

fun Route.healthRoutes() {
    route("/health") {
        get {
            call.respond(HttpStatusCode.OK, mapOf("status" to "ok"))
        }
    }
}
