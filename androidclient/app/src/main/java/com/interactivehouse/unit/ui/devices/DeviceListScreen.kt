package com.interactivehouse.unit.ui.devices

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.interactivehouse.unit.data.models.Device

@Composable
fun DeviceListScreen(
    devices: List<Device>,
    deviceStates: Map<String, Map<String, Any>>,
    isLoading: Boolean,
    error: String?,
    onRefresh: () -> Unit,
    onSelect: (Device) -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Text("Devices", style = MaterialTheme.typography.headlineMedium)
            TextButton(onClick = onRefresh, enabled = !isLoading) { Text("Refresh") }
        }

        if (!error.isNullOrBlank()) {
            Spacer(Modifier.height(8.dp))
            Text(error, color = MaterialTheme.colorScheme.error)
        }

        Spacer(Modifier.height(12.dp))

        if (isLoading && devices.isEmpty()) {
            CircularProgressIndicator()
            return
        }

        LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp)) {
            items(devices) { d ->
                val st = deviceStates[d.deviceId]
                val statusText = statusFor(d.deviceType, st)

                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable { onSelect(d) }
                ) {
                    Column(Modifier.padding(14.dp)) {
                        Text(friendlyName(d.deviceType), style = MaterialTheme.typography.titleMedium)
                        Spacer(Modifier.height(2.dp))
                        Text("ID: ${d.deviceId}", style = MaterialTheme.typography.bodyMedium)
                        Spacer(Modifier.height(6.dp))
                        Text(statusText, style = MaterialTheme.typography.bodyMedium)
                    }
                }
            }
        }
    }
}

private fun friendlyName(deviceType: String): String =
    when (deviceType.lowercase()) {
        "light" -> "Light"
        "doorlock" -> "Door Lock"
        "coffeemachine" -> "Coffee Machine"
        else -> deviceType
    }

private fun statusFor(deviceType: String, state: Map<String, Any>?): String {
    if (state == null) return "Status: unknown"

    val t = deviceType
        .trim()
        .lowercase()
        .replace("_", "")
        .replace("-", "")
        .replace(" ", "")

    return when (t) {
        "light" -> {
            val on = state["lightOn"] as? Boolean
            if (on == true) "Status: ON" else "Status: OFF"
        }
        "doorlock", "lock" -> {
            val locked = state["locked"] as? Boolean
            if (locked == true) "Status: LOCKED" else "Status: UNLOCKED"
        }
        "coffeemachine", "coffee" -> {
            val making = state["isMaking"] as? Boolean
            if (making == true) "Status: MAKING…" else "Status: READY"
        }
        else -> "Status: $state"
    }
}