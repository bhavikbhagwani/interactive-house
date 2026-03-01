package com.interactivehouse.unit.data.repo

import com.interactivehouse.unit.data.models.Device
import com.interactivehouse.unit.data.models.UiDefinition
import kotlinx.coroutines.flow.Flow

interface SmartHomeRepository {
    suspend fun login(username: String, password: String): Boolean
    suspend fun getDevices(): List<Device>
    suspend fun getUi(deviceId: String): UiDefinition
    fun stateUpdates(deviceId: String): Flow<Map<String, Any>>
    suspend fun sendAction(deviceId: String, action: String)
}