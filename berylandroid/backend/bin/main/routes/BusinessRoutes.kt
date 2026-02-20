import io.ktor.server.routing.Route
import io.ktor.server.routing.post
import io.ktor.server.routing.route
import io.ktor.server.application.call
import io.ktor.server.request.receive
import io.ktor.server.response.respond

fun Route.businessRoutes(
    businessService: BusinessService,
    validationService: ValidationService
) {
    route("/business") {
        post("/compute") {
            val request = call.receive<BusinessComputeRequest>()
            validationService.validateBusinessRequest(request)
            val response = businessService.compute(request)
            call.respond(response)
        }
    }
}
