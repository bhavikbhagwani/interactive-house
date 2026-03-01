package com.interactivehouse.unit.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.interactivehouse.unit.data.models.Device
import com.interactivehouse.unit.data.models.UiDefinition
import com.interactivehouse.unit.data.repo.SmartHomeRepository
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

data class UiState(
    val isLoggedIn: Boolean = false,
    val isLoading: Boolean = false,
    val loginError: String? = null,
    val devices: List<Device> = emptyList(),
    val selectedDevice: Device? = null,
    val uiDefinition: UiDefinition? = null,
    val latestState: Map<String, Any> = emptyMap(),
    val deviceStates: Map<String, Map<String, Any>> = emptyMap(),
    val error: String? = null
)

class SmartHomeViewModel(private val repo: SmartHomeRepository) : ViewModel() {

    private val _state = MutableStateFlow(UiState())
    val state: StateFlow<UiState> = _state.asStateFlow()

    private var updatesJob: Job? = null

    fun login(username: String, password: String) {
        viewModelScope.launch {
            _state.update { it.copy(isLoading = true, loginError = null) }
            val ok = repo.login(username, password)
            if (ok) {
                _state.update { it.copy(isLoggedIn = true, isLoading = false) }
                loadDevices()
            } else {
                _state.update { it.copy(isLoading = false, loginError = "login_failed") }
            }
        }
    }

    fun loadDevices() {
        viewModelScope.launch {
            _state.update { it.copy(isLoading = true, error = null) }
            runCatching { repo.getDevices() }
                .onSuccess { devs -> _state.update { it.copy(isLoading = false, devices = devs) } }
                .onFailure { e -> _state.update { it.copy(isLoading = false, error = e.message) } }
        }
    }

    fun selectDevice(device: Device) {
        viewModelScope.launch {
            _state.update { it.copy(selectedDevice = device, uiDefinition = null, latestState = emptyMap()) }
            val ui = repo.getUi(device.deviceId)
            _state.update { it.copy(uiDefinition = ui) }

            updatesJob?.cancel()
            updatesJob = launch {
                repo.stateUpdates(device.deviceId).collect { st ->
                    _state.update {
                        it.copy(
                            latestState = st,
                            deviceStates = it.deviceStates + (device.deviceId to st)
                        )
                    }
                }
            }
        }
    }

    fun sendAction(action: String) {
        val deviceId = _state.value.selectedDevice?.deviceId ?: return
        viewModelScope.launch {
            runCatching { repo.sendAction(deviceId, action) }
                .onFailure { e -> _state.update { it.copy(error = e.message ?: "error") } }
        }
    }

    fun backToList() {
        updatesJob?.cancel()
        _state.update { it.copy(selectedDevice = null, uiDefinition = null, latestState = emptyMap()) }
    }
}