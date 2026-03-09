package com.interactivehouse.unit.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.interactivehouse.unit.data.models.Device
import com.interactivehouse.unit.data.models.UiDefinition
import com.interactivehouse.unit.data.repo.SmartHomeRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

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

    fun login(email: String, password: String) {
        viewModelScope.launch {
            _state.update { it.copy(isLoading = true, loginError = null) }

            val ok = withContext(Dispatchers.IO) {
                repo.login(email, password)
            }

            if (ok) {
                _state.update { it.copy(isLoggedIn = true, isLoading = false) }
                loadDevices()
            } else {
                _state.update { it.copy(isLoading = false, loginError = "Invalid email or password") }
            }
        }
    }

    fun loadDevices() {
        viewModelScope.launch {
            _state.update { it.copy(isLoading = true, error = null) }

            runCatching {
                withContext(Dispatchers.IO) {
                    repo.getDevices()
                }
            }
                .onSuccess { devs ->
                    _state.update { it.copy(isLoading = false, devices = devs) }
                }
                .onFailure { e ->
                    _state.update { it.copy(isLoading = false, error = e.message) }
                }
        }
    }

    fun selectDevice(device: Device) {
        viewModelScope.launch {
            _state.update {
                it.copy(
                    selectedDevice = device,
                    uiDefinition = null,
                    latestState = emptyMap(),
                    error = null
                )
            }

            runCatching {
                withContext(Dispatchers.IO) {
                    repo.getUi(device.deviceId)
                }
            }
                .onSuccess { ui ->
                    android.util.Log.d("SmartHomeVM", "UI initialState for ${device.deviceId} = ${ui.initialState}")

                    _state.update {
                        it.copy(
                            uiDefinition = ui,
                            latestState = ui.initialState,
                            deviceStates = it.deviceStates + (device.deviceId to ui.initialState)
                        )
                    }

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
                .onFailure { e ->
                    _state.update { it.copy(error = e.message ?: "Failed to load device UI") }
                }
        }
    }

    fun sendAction(action: String) {
        val deviceId = _state.value.selectedDevice?.deviceId ?: return

        viewModelScope.launch(Dispatchers.IO) {
            runCatching { repo.sendAction(deviceId, action) }
                .onFailure { e ->
                    _state.update { it.copy(error = e.message ?: "error") }
                }
        }
    }

    fun backToList() {
        updatesJob?.cancel()
        _state.update {
            it.copy(selectedDevice = null, uiDefinition = null, latestState = emptyMap())
        }
    }
}