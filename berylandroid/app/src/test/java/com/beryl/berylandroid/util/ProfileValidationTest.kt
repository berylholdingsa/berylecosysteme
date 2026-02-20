package com.beryl.berylandroid.util

import kotlin.test.assertFalse
import kotlin.test.assertTrue
import org.junit.Test

class ProfileValidationTest {

    @Test
    fun `valid email is accepted`() {
        assertTrue(ProfileValidation.isEmailValid("amila@beryl.ci"))
    }

    @Test
    fun `invalid email is rejected`() {
        assertFalse(ProfileValidation.isEmailValid("amila"))
    }

    @Test
    fun `valid phone in E164 is accepted`() {
        assertTrue(ProfileValidation.isPhoneValid("+2250123456789"))
    }

    @Test
    fun `invalid phone is rejected`() {
        assertFalse(ProfileValidation.isPhoneValid("012345"))
    }
}
