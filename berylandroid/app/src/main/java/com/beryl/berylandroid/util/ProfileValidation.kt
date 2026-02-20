package com.beryl.berylandroid.util

object ProfileValidation {
    private val phoneRegex = Regex("^\\+[1-9]\\d{1,14}$")
    private val emailRegex =
        Regex("^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}\$", RegexOption.IGNORE_CASE)

    fun isEmailValid(email: String?): Boolean {
        return !email.isNullOrBlank() && emailRegex.matches(email.trim())
    }

    fun isPhoneValid(phone: String?): Boolean {
        return !phone.isNullOrBlank() && phoneRegex.matches(phone.trim())
    }
}
