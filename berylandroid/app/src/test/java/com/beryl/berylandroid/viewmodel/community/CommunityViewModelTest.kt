package com.beryl.berylandroid.viewmodel.community

import kotlin.test.assertEquals
import org.junit.Test

class CommunityViewModelTest {

    @Test
    fun `clampDebounceMs clamps below min`() {
        assertEquals(0L, CommunityViewModel.clampDebounceMs(-120L))
    }

    @Test
    fun `clampDebounceMs keeps in-range values`() {
        assertEquals(250L, CommunityViewModel.clampDebounceMs(250L))
    }

    @Test
    fun `clampDebounceMs clamps above max`() {
        assertEquals(2_000L, CommunityViewModel.clampDebounceMs(5_000L))
    }
}
