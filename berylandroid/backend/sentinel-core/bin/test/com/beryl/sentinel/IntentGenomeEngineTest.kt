package com.beryl.sentinel

import com.beryl.sentinel.engine.IntentGenomeEngine
import kotlin.test.Test
import kotlin.test.assertEquals

class IntentGenomeEngineTest {
    private val engine = IntentGenomeEngine()

    @Test
    fun `detect payment intent`() {
        val intent = engine.detectIntent("Je veux transférer 1000 francs via BerylPay")
        assertEquals("payment", intent.name)
    }
}
