package com.beryl.berylandroid.viewmodel.mobility

import androidx.lifecycle.ViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update

private val sampleRoute = listOf(
    GeoPoint(5.345, -4.024),
    GeoPoint(5.349, -4.022),
    GeoPoint(5.356, -4.019),
    GeoPoint(5.364, -4.015),
    GeoPoint(5.372, -4.011)
)

private val previewRoute = listOf(
    GeoPoint(5.345, -4.024),
    GeoPoint(5.352, -4.030),
    GeoPoint(5.360, -4.028),
    GeoPoint(5.372, -4.011)
)

class MobilityViewModel : ViewModel() {
    private val _uiState = MutableStateFlow(
        MobilityUiState(
            destinationQuery = "Plateau, Abidjan",
            frequentDestinations = listOf("Cocody Riviera", "Marcory Zone 4", "Plateau - Immeuble AXA"),
            aiSuggestions = listOf("Maison · 18:30", "Travail · 08:10", "Aéroport · 06:00"),
            recommendedVehicle = "Beryl E-Prime",
            nearestVehicle = "Beryl Onyx",
            priceEstimate = "4 900 XOF",
            etaMinutes = 12,
            remainingRangeKm = 86,
            batteryPercent = 74,
            co2AvoidedKg = 2.4,
            chargingStations = listOf(
                ChargingStation("CS-01", "Station VRD", GeoPoint(5.357, -4.020)),
                ChargingStation("CS-02", "Pont HKB", GeoPoint(5.365, -4.018)),
                ChargingStation("CS-03", "Béryl Hub", GeoPoint(5.372, -4.012))
            ),
            route = sampleRoute,
            previewRoute = previewRoute,
            trafficLevel = TrafficLevel.MODERATE,
            payAmount = "4 900 XOF",
            energyStops = 1,
            passengerName = "Koffi",
            passengerPhone = "+225 07 12 34 56 78"
        )
    )

    val uiState: StateFlow<MobilityUiState> = _uiState

    fun updateDestination(query: String) {
        _uiState.update { it.copy(destinationQuery = query) }
    }

    fun applySuggestion(suggestion: String) {
        _uiState.update { it.copy(destinationQuery = suggestion) }
    }

    fun setEcoOptimized(enabled: Boolean) {
        _uiState.update { it.copy(ecoOptimized = enabled) }
    }

    fun updatePaymentMethod(method: PaymentMethod) {
        _uiState.update { it.copy(paymentMethod = method) }
    }

    fun markPaid() {
        _uiState.update { it.copy(paymentStatus = PaymentStatus.Confirmed) }
    }
}

enum class TrafficLevel {
    LOW,
    MODERATE,
    HIGH
}

enum class PaymentMethod {
    BERYL_PAY,
    MOBILE_MONEY,
    CARD
}

enum class PaymentStatus {
    Idle,
    Confirmed
}

data class ChargingStation(
    val id: String,
    val name: String,
    val position: GeoPoint
)

data class GeoPoint(
    val latitude: Double,
    val longitude: Double
)

data class MobilityUiState(
    val destinationQuery: String,
    val frequentDestinations: List<String>,
    val aiSuggestions: List<String>,
    val recommendedVehicle: String,
    val nearestVehicle: String,
    val priceEstimate: String,
    val etaMinutes: Int,
    val remainingRangeKm: Int,
    val batteryPercent: Int,
    val co2AvoidedKg: Double,
    val chargingStations: List<ChargingStation>,
    val route: List<GeoPoint>,
    val previewRoute: List<GeoPoint>,
    val trafficLevel: TrafficLevel,
    val payAmount: String,
    val energyStops: Int,
    val passengerName: String,
    val passengerPhone: String,
    val ecoOptimized: Boolean = true,
    val paymentMethod: PaymentMethod = PaymentMethod.BERYL_PAY,
    val paymentStatus: PaymentStatus = PaymentStatus.Idle
)
