class UserService(private val repository: UserRepository) {
    suspend fun getOrCreate(authUser: AuthenticatedUser): UserDto {
        val existing = repository.getById(authUser.uid)
        val now = System.currentTimeMillis()

        val user = if (existing == null) {
            UserDomain(
                uid = authUser.uid,
                email = authUser.email,
                displayName = authUser.name,
                createdAt = now,
                updatedAt = now
            )
        } else {
            existing.copy(
                email = authUser.email ?: existing.email,
                displayName = authUser.name ?: existing.displayName,
                updatedAt = now
            )
        }

        val saved = repository.upsert(user)
        return UserDto(
            uid = saved.uid,
            email = saved.email,
            displayName = saved.displayName,
            createdAt = saved.createdAt,
            updatedAt = saved.updatedAt
        )
    }
}
