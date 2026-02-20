package com.beryl.berylandroid.model.community

data class CommunityStatus(
    val id: String,
    val owner: String,
    val subtitle: String,
    val timestamp: String,
    val progress: Float,
    val isNew: Boolean = true,
    val conversationId: String? = null
)

data class CommunityGroup(
    val id: String,
    val name: String,
    val role: CommunityRole,
    val memberCount: Int,
    val lastActivity: String,
    val unreadHighlights: Int = 0
)

enum class CommunityRole(val label: String) {
    ADMIN("Admin"),
    MEMBER("Membre")
}

enum class SuperAppModule(val label: String) {
    MOBILITE("Mobilité"),
    BERYLPAY("BérylPay"),
    ESG("Impact")
}

data class SuperAppLink(
    val id: String,
    val title: String,
    val description: String,
    val module: SuperAppModule
)

data class AiInsight(
    val id: String,
    val title: String,
    val summary: String,
    val highlightMessage: String,
    val conversationId: String
)
