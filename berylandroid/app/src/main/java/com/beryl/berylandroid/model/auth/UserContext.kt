package com.beryl.berylandroid.model.auth

import com.beryl.sentinel.sdk.SentinelUserContext

fun UserProfile.toSentinelUserContext(): SentinelUserContext {
    return SentinelUserContext(
        firstName = firstName,
        role = role.name,
        kycStatus = kycStatus.name,
        riskScore = riskScore
    )
}

fun UserProfile?.toSentinelUserContextOrDefault(): SentinelUserContext {
    return this?.toSentinelUserContext() ?: SentinelUserContext()
}
