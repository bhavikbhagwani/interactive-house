package com.interactivehouse.unit.data.repo

import com.interactivehouse.unit.data.models.*
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.asSharedFlow

class FakeSmartHomeRepository : SmartHomeRepository {

    private val flows = mutableMapOf<String, MutableSharedFlow<Map<String, Any>>>()
    private fun flowFor(deviceId: String) =
        flows.getOrPut(deviceId) { MutableSharedFlow(replay = 1) }

    override suspend fun login(username: String, password: String): Boolean {
        delay(250)
        return username.isNotBlank() && password.isNotBlank()
    }

    override suspend fun getDevices(): List<Device> {
        delay(250)
        return listOf(
            Device("light-1", "Light"),
            Device("lock-1", "Door Lock"),
            Device("coffee-1", "Coffee Machine")
        )
    }

    override suspend fun getUi(deviceId: String): UiDefinition {
        delay(150)
        return when (deviceId) {
            "light-1" -> UiDefinition("Light", listOf(
                Control("button", "ON", "LIGHT_ON"),
                Control("button", "OFF", "LIGHT_OFF")
            ))
            "lock-1" -> UiDefinition("Door Lock", listOf(
                Control("button", "LOCK", "LOCK"),
                Control("button", "UNLOCK", "UNLOCK")
            ))
            else -> UiDefinition("Coffee Machine", listOf(
                Control("button", "MAKE", "MAKE",
                    disabledWhen = DisabledWhen("isMaking", true)
                )
            ))
        }
    }

    override fun stateUpdates(deviceId: String): Flow<Map<String, Any>> =
        flowFor(deviceId).asSharedFlow()

    override suspend fun sendAction(deviceId: String, action: String) {
        val f = flowFor(deviceId)
        when (deviceId) {
            "light-1" -> f.emit(mapOf("lightOn" to (action == "LIGHT_ON")))
            "lock-1" -> f.emit(mapOf("locked" to (action == "LOCK")))
            "coffee-1" -> if (action == "MAKE") {
                f.emit(mapOf("isMaking" to true))
                delay(3000)
                f.emit(mapOf("isMaking" to false))
            }
        }
    }
}