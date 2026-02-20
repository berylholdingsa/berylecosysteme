import kotlin.math.absoluteValue

class BusinessService {
    fun compute(request: BusinessComputeRequest): BusinessComputeResponse {
        val base = request.signal.hashCode().absoluteValue % 100
        val factorScore = request.factors.sum().absoluteValue % 100
        val weighted = (base * 0.6 + request.weight * 0.3 + factorScore * 0.1)
        val score = weighted.toInt().coerceIn(0, 100)
        val decision = if (score >= 60) "approve" else "review"
        val rationale = "score=$score base=$base weight=${request.weight} factors=${request.factors.size}"
        return BusinessComputeResponse(score, decision, rationale)
    }
}
