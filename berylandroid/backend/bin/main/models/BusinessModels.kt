import kotlinx.serialization.Serializable

@Serializable
data class BusinessComputeRequest(
    val signal: String,
    val weight: Int,
    val factors: List<Int> = emptyList()
)

@Serializable
data class BusinessComputeResponse(
    val score: Int,
    val decision: String,
    val rationale: String
)
