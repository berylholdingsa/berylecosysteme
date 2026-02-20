package com.beryl.esg.ui.state

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.beryl.esg.data.repository.GreenOSImpactConfidenceResponse
import com.beryl.esg.data.repository.GreenOSImpactResponse
import com.beryl.esg.data.repository.GreenOSImpactVerificationResponse
import com.beryl.esg.data.repository.GreenOSMethodologyResponse
import com.beryl.esg.data.repository.GreenOSMrvConfidenceSummaryResponse
import com.beryl.esg.data.repository.GreenOSMrvExportResponse
import com.beryl.esg.data.repository.GreenOSRealtimeCalculateRequest
import com.beryl.esg.data.repository.GreenOSRepositoryResult
import com.beryl.esg.data.repository.GreenOSRepositoryV2
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

class ESGViewModel(
    private val repository: GreenOSRepositoryV2 = GreenOSRepositoryV2()
) : ViewModel() {

    private val _homeState = MutableStateFlow<ESGUiState<ESGHomeContent>>(ESGUiState.Loading)
    val homeState: StateFlow<ESGUiState<ESGHomeContent>> = _homeState

    private val _impactState = MutableStateFlow<ESGUiState<ESGImpactDetailContent>>(ESGUiState.Loading)
    val impactState: StateFlow<ESGUiState<ESGImpactDetailContent>> = _impactState

    private val _confidenceState = MutableStateFlow<ESGUiState<ESGConfidenceContent>>(ESGUiState.Loading)
    val confidenceState: StateFlow<ESGUiState<ESGConfidenceContent>> = _confidenceState

    private val _verificationState = MutableStateFlow<ESGUiState<ESGVerificationContent>>(ESGUiState.Loading)
    val verificationState: StateFlow<ESGUiState<ESGVerificationContent>> = _verificationState

    private val _mrvReportState = MutableStateFlow<ESGUiState<ESGMrvReportContent>>(ESGUiState.Loading)
    val mrvReportState: StateFlow<ESGUiState<ESGMrvReportContent>> = _mrvReportState

    private val _methodologyState = MutableStateFlow<ESGUiState<ESGMethodologyContent>>(ESGUiState.Loading)
    val methodologyState: StateFlow<ESGUiState<ESGMethodologyContent>> = _methodologyState

    fun loadHome(
        period: String = "3M",
        activeTrip: GreenOSRealtimeCalculateRequest? = null
    ) {
        _homeState.value = ESGUiState.Loading
        viewModelScope.launch {
            if (activeTrip != null) {
                when (val realtimeResult = repository.calculateRealtime(activeTrip)) {
                    is GreenOSRepositoryResult.Error -> {
                        _homeState.value = ESGUiState.Error(realtimeResult.code)
                        return@launch
                    }

                    GreenOSRepositoryResult.Empty -> {
                        _homeState.value = ESGUiState.Empty
                        return@launch
                    }

                    is GreenOSRepositoryResult.Success -> Unit
                }
            }

            when (val exportResult = repository.getMrvExport(period)) {
                is GreenOSRepositoryResult.Success -> {
                    val content = mapHomeContent(exportResult.data)
                    _homeState.value = if (content == null) {
                        ESGUiState.Empty
                    } else {
                        ESGUiState.Content(content)
                    }
                }

                GreenOSRepositoryResult.Empty -> {
                    _homeState.value = ESGUiState.Empty
                }

                is GreenOSRepositoryResult.Error -> {
                    _homeState.value = ESGUiState.Error(exportResult.code)
                }
            }
        }
    }

    fun loadImpact(tripId: String) {
        _impactState.value = ESGUiState.Loading
        viewModelScope.launch {
            when (val result = repository.getImpact(tripId)) {
                is GreenOSRepositoryResult.Success -> {
                    val content = mapImpactContent(result.data)
                    _impactState.value = if (content == null) ESGUiState.Empty else ESGUiState.Content(content)
                }

                GreenOSRepositoryResult.Empty -> {
                    _impactState.value = ESGUiState.Empty
                }

                is GreenOSRepositoryResult.Error -> {
                    _impactState.value = ESGUiState.Error(result.code)
                }
            }
        }
    }

    fun loadConfidence(tripId: String) {
        _confidenceState.value = ESGUiState.Loading
        viewModelScope.launch {
            when (val result = repository.getImpactConfidence(tripId)) {
                is GreenOSRepositoryResult.Success -> {
                    val content = mapConfidenceContent(result.data)
                    _confidenceState.value = if (content == null) ESGUiState.Empty else ESGUiState.Content(content)
                }

                GreenOSRepositoryResult.Empty -> {
                    _confidenceState.value = ESGUiState.Empty
                }

                is GreenOSRepositoryResult.Error -> {
                    _confidenceState.value = ESGUiState.Error(result.code)
                }
            }
        }
    }

    fun loadVerification(tripId: String) {
        _verificationState.value = ESGUiState.Loading
        viewModelScope.launch {
            when (val result = repository.getImpactVerification(tripId)) {
                is GreenOSRepositoryResult.Success -> {
                    val content = mapVerificationContent(result.data)
                    _verificationState.value = if (content == null) ESGUiState.Empty else ESGUiState.Content(content)
                }

                GreenOSRepositoryResult.Empty -> {
                    _verificationState.value = ESGUiState.Empty
                }

                is GreenOSRepositoryResult.Error -> {
                    _verificationState.value = ESGUiState.Error(result.code)
                }
            }
        }
    }

    fun loadMrvReport(period: String = "3M") {
        _mrvReportState.value = ESGUiState.Loading
        viewModelScope.launch {
            when (val exportResult = repository.getMrvExport(period)) {
                is GreenOSRepositoryResult.Success -> {
                    val export = exportResult.data
                    val exportId = export.exportId
                    if (exportId.isNullOrBlank()) {
                        _mrvReportState.value = ESGUiState.Empty
                        return@launch
                    }

                    when (val confidenceResult = repository.getMrvConfidenceSummary(exportId)) {
                        is GreenOSRepositoryResult.Success -> {
                            val content = mapMrvReportContent(export, confidenceResult.data)
                            _mrvReportState.value = if (content == null) {
                                ESGUiState.Empty
                            } else {
                                ESGUiState.Content(content)
                            }
                        }

                        GreenOSRepositoryResult.Empty -> {
                            _mrvReportState.value = ESGUiState.Empty
                        }

                        is GreenOSRepositoryResult.Error -> {
                            _mrvReportState.value = ESGUiState.Error(confidenceResult.code)
                        }
                    }
                }

                GreenOSRepositoryResult.Empty -> {
                    _mrvReportState.value = ESGUiState.Empty
                }

                is GreenOSRepositoryResult.Error -> {
                    _mrvReportState.value = ESGUiState.Error(exportResult.code)
                }
            }
        }
    }

    fun loadMethodology() {
        _methodologyState.value = ESGUiState.Loading
        viewModelScope.launch {
            when (val result = repository.getCurrentMethodology()) {
                is GreenOSRepositoryResult.Success -> {
                    val content = mapMethodologyContent(result.data)
                    _methodologyState.value = if (content == null) ESGUiState.Empty else ESGUiState.Content(content)
                }

                GreenOSRepositoryResult.Empty -> {
                    _methodologyState.value = ESGUiState.Empty
                }

                is GreenOSRepositoryResult.Error -> {
                    _methodologyState.value = ESGUiState.Error(result.code)
                }
            }
        }
    }

    private fun mapHomeContent(response: GreenOSMrvExportResponse): ESGHomeContent? {
        val totalCo2 = response.totalCo2Avoided ?: return null
        val totalDistance = response.totalDistance ?: return null
        val confidencePayload = response.payload?.confidenceSummary ?: return null
        val aoqStatus = confidencePayload.aoqStatus?.takeIf { it.isNotBlank() } ?: return null
        val averageConfidence = confidencePayload.averageConfidence ?: return null
        val modelVersion = response.payload?.methodology?.modelVersion
            ?.takeIf { it.isNotBlank() }
            ?: response.payload?.modelVersions?.firstOrNull()?.takeIf { it.isNotBlank() }
            ?: return null

        return ESGHomeContent(
            totalCo2Avoided = totalCo2,
            totalDistance = totalDistance,
            aoqStatus = aoqStatus,
            averageConfidence = averageConfidence,
            modelVersion = modelVersion
        )
    }

    private fun mapImpactContent(response: GreenOSImpactResponse): ESGImpactDetailContent? {
        val co2 = response.co2AvoidedKg ?: return null
        val distance = response.distanceKm ?: return null
        val country = response.countryCode?.takeIf { it.isNotBlank() } ?: return null
        val hash = response.eventHash?.takeIf { it.isNotBlank() } ?: return null
        val signatureAlgorithm = response.signatureAlgorithm?.takeIf { it.isNotBlank() } ?: return null
        val modelVersion = response.modelVersion?.takeIf { it.isNotBlank() } ?: return null

        return ESGImpactDetailContent(
            co2AvoidedKg = co2,
            distanceKm = distance,
            countryCode = country,
            eventHash = hash,
            signatureAlgorithm = signatureAlgorithm,
            modelVersion = modelVersion
        )
    }

    private fun mapConfidenceContent(response: GreenOSImpactConfidenceResponse): ESGConfidenceContent? {
        val confidenceScore = response.confidenceScore ?: return null
        val integrityIndex = response.integrityIndex ?: return null
        val aoqStatus = response.aoqStatus?.takeIf { it.isNotBlank() } ?: return null
        val anomalyFlags = response.anomalyFlags ?: return null

        return ESGConfidenceContent(
            confidenceScore = confidenceScore,
            integrityIndex = integrityIndex,
            aoqStatus = aoqStatus,
            anomalyFlags = anomalyFlags
        )
    }

    private fun mapVerificationContent(response: GreenOSImpactVerificationResponse): ESGVerificationContent? {
        val verified = response.verified ?: return null
        val hashValid = response.eventHashValid ?: return null
        val signatureValid = response.signatureValid ?: return null
        val asymSignatureValid = response.asymSignatureValid ?: return null

        return ESGVerificationContent(
            verified = verified,
            hashValid = hashValid,
            signatureValid = signatureValid,
            asymSignatureValid = asymSignatureValid
        )
    }

    private fun mapMrvReportContent(
        exportResponse: GreenOSMrvExportResponse,
        confidenceResponse: GreenOSMrvConfidenceSummaryResponse
    ): ESGMrvReportContent? {
        val totalCo2 = exportResponse.totalCo2Avoided ?: return null
        val methodologyVersion = exportResponse.methodologyVersion?.takeIf { it.isNotBlank() } ?: return null
        val averageConfidence = confidenceResponse.averageConfidence ?: return null
        val aoqStatus = confidenceResponse.aoqStatus?.takeIf { it.isNotBlank() } ?: return null

        return ESGMrvReportContent(
            totalCo2Avoided = totalCo2,
            methodologyVersion = methodologyVersion,
            averageConfidence = averageConfidence,
            aoqStatus = aoqStatus
        )
    }

    private fun mapMethodologyContent(response: GreenOSMethodologyResponse): ESGMethodologyContent? {
        val methodologyVersion = response.methodologyVersion?.takeIf { it.isNotBlank() } ?: return null
        val emissionFactorSource = response.emissionFactorSource?.takeIf { it.isNotBlank() } ?: return null
        val geographicScope = response.geographicScope?.takeIf { it.isNotBlank() } ?: return null
        val status = response.status?.takeIf { it.isNotBlank() } ?: return null

        return ESGMethodologyContent(
            methodologyVersion = methodologyVersion,
            emissionFactorSource = emissionFactorSource,
            geographicScope = geographicScope,
            status = status
        )
    }
}
