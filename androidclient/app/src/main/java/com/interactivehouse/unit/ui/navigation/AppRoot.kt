package com.interactivehouse.unit.ui.navigation


import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import com.interactivehouse.unit.ui.SmartHomeViewModel
import com.interactivehouse.unit.ui.devices.DeviceListScreen
import com.interactivehouse.unit.ui.dynamic.DeviceScreen
import com.interactivehouse.unit.ui.login.LoginScreen


@Composable
fun AppRoot(vm: SmartHomeViewModel) {
    val state by vm.state.collectAsState()


    when {
        !state.isLoggedIn -> {
            LoginScreen(
                isLoading = state.isLoading,
                error = state.loginError,
                onLogin = vm::login
            )
        }


        state.selectedDevice == null -> {
            DeviceListScreen(
                devices = state.devices,
                deviceStates = state.deviceStates,
                isLoading = state.isLoading,
                error = state.error,
                statusMessage = state.statusMessage,
                onRefresh = vm::loadDevices,
                onSelect = vm::selectDevice,
                onTriggerScene = vm::triggerScene,
                onVoiceCommand = vm::sendVoiceCommand,
                onClearMessage = vm::clearStatusMessage
            )
        }


        else -> {
            val selected = state.selectedDevice ?: return


            DeviceScreen(
                title = selected.deviceId,
                uiDefinition = state.uiDefinition,
                latestState = state.latestState,
                error = state.error,
                onBack = vm::backToList,
                onAction = vm::sendAction
            )
        }
    }
}

