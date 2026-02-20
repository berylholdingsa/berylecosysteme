import io.ktor.server.routing.Route
import io.ktor.server.routing.get
import io.ktor.server.routing.post
import io.ktor.server.routing.route
import io.ktor.server.application.call
import io.ktor.server.request.receive
import io.ktor.server.response.respond

fun Route.communityRoutes(
    communityService: CommunityService,
    validationService: ValidationService
) {
    route("/community") {
        post("/post") {
            val authUser = call.attributes[AuthenticatedUserKey]
            val request = call.receive<CommunityPostRequest>()
            validationService.validateCommunityPost(request)
            val response = communityService.createPost(authUser.uid, request)
            call.respond(response)
        }
        get("/feed") {
            val limitParam = call.request.queryParameters["limit"] ?: "20"
            val limit = limitParam.toIntOrNull()?.coerceIn(1, 50) ?: 20
            val response = communityService.feed(limit)
            call.respond(response)
        }
    }
}
