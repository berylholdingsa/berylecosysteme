class ValidationService {
    fun validateBusinessRequest(request: BusinessComputeRequest) {
        if (request.signal.isBlank() || request.signal.length < 3) {
            throw ValidationException("signal must be at least 3 characters")
        }
        if (request.weight !in 1..100) {
            throw ValidationException("weight must be between 1 and 100")
        }
        if (request.factors.size > 20) {
            throw ValidationException("factors size limit exceeded")
        }
        request.factors.forEach {
            if (it !in 0..100) {
                throw ValidationException("factor values must be between 0 and 100")
            }
        }
    }

    fun validateCommunityPost(request: CommunityPostRequest) {
        if (request.content.isBlank() || request.content.length < 5) {
            throw ValidationException("content must be at least 5 characters")
        }
        if (request.content.length > 2000) {
            throw ValidationException("content exceeds 2000 characters")
        }
        if (request.tags.size > 10) {
            throw ValidationException("too many tags")
        }
    }
}
